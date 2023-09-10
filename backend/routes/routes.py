from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import base64
import time
from fastapi import BackgroundTasks
from collections import deque
from background_tasks.tasks import perform_detection, resize_and_encode_frame, detect_faces, detect_objects, save_frame, apply_night_vision
from models.models import Settings, Recordings, VideoPreviews
from helpers.settings_methods import load_settings_from_file, save_settings_to_file
from helpers.cameras import get_available_cameras

routes = APIRouter()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

@routes.get("/video_feed_previews", response_model=VideoPreviews)
async def get_video_feed():
    available_cameras = get_available_cameras()
    frames = {}
    
    for camera_id in available_cameras:
        cap = cv2.VideoCapture(camera_id)
        ret, frame = cap.read()
        
        if ret:
            to_send = resize_and_encode_frame(frame)
            frames[camera_id] = base64.b64encode(to_send).decode('utf-8')
        
        cap.release()

    return VideoPreviews(frames=frames)

@routes.get("/settings")
async def get_system_settings():
    current_settings = load_settings_from_file()
    return current_settings

@routes.post("/settings")
async def update_system_settings(settings: Settings):
    save_settings_to_file(settings)
    return {"message": "Settings updated"}

@routes.post("/toggle_facial_recognition")
async def toggle_facial_recognition():
    settings = load_settings_from_file()
    settings.FacialRecognitionEnabled = not settings.FacialRecognitionEnabled
    save_settings_to_file(settings)
    return {"message": "Facial recognition toggled", "new_state": settings.FacialRecognitionEnabled}

@routes.post("/toggle_night_vision")
async def toggle_night_vision():
    settings = load_settings_from_file()
    settings.NightVisionEnabled = not settings.NightVisionEnabled
    save_settings_to_file(settings)
    return {"message": "Night vision toggled", "new_state": settings.NightVisionEnabled}

@routes.get("/recordings")
async def get_recordings():
    # Your logic to get the list of recordings
    files = ["file1.mp4", "file2.mp4"]  # Example
    return Recordings(files=files)

@routes.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, background_tasks: BackgroundTasks):
    await websocket.accept()
    
    skip_frames = 2  # Perform detection every 3rd frame
    frame_count = 0
    
    available_cameras = get_available_cameras()
    
    if len(available_cameras) == 0:
        print('No cameras available')
        connection_closed = True
        await websocket.close()
        return
    
    cap = cv2.VideoCapture(available_cameras[0])
    connection_closed = False

    # Initialize YOLO
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
    

    frame_rate = 30  # Assuming 30 FPS for the webcam
    frame_window = frame_rate * 5  # Number of frames for 5 seconds
    frames = deque(maxlen=frame_window)  # Fixed-size queue to store frames

    try:
        while True:
            if connection_closed:
                break
             
            start_time = time.time()  # Time measurement

            ret, frame = cap.read()

            # Add the captured frame to the deque
            frames.append(frame)
            
            frame = apply_night_vision(frame)
            
            # background_tasks.add_task(
            #     perform_detection, frame, net, face_cascade, frame_count, skip_frames)
            frame = detect_faces(frame, face_cascade)
            
            try:
                to_send = resize_and_encode_frame(frame)
                
                await websocket.send_text(base64.b64encode(to_send).decode('utf-8'))
            except Exception as e:
                print(f"Frame encoding or sending failed: {e }")
                connection_closed = True
                cap.release()
                print("WebSocket disconnected, webcam released")
                await websocket.close()

            frame_count += 1
            end_time = time.time()  # Time measurement
            # print(f"Time taken for a loop: {end_time - start_time}")
    except WebSocketDisconnect:
        connection_closed = True
        cap.release()
        print("WebSocket disconnected, webcam released")
        await websocket.close()
    