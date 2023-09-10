from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import base64
import time
from fastapi import BackgroundTasks
from collections import deque
from fastapi.responses import JSONResponse
from background_tasks.tasks import perform_detection, resize_and_encode_frame, detect_faces, detect_objects, save_frame, apply_night_vision
from models.models import Settings, Recordings, VideoPreviews
from helpers.settings_methods import load_settings_from_file, save_settings_to_file
from helpers.cameras import get_available_cameras
import asyncio
import threading

routes = APIRouter()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

routes = APIRouter()
frames = {}
frame_locks = {}
monitoring_flags = {}

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

@routes.post("/start_monitoring/{camera_id}")
async def start_monitoring(camera_id: int):
    if camera_id not in frames:
        frames[camera_id] = None
        frame_locks[camera_id] = threading.Lock()
        monitoring_flags[camera_id] = True  # Set the flag
        threading.Thread(target=start_camera, args=(camera_id,)).start()
        return JSONResponse(content={"message": f"Started monitoring camera {camera_id}"})
    else:
        return JSONResponse(content={"message": f"Already monitoring camera {camera_id}"})


@routes.post("/stop_monitoring/{camera_id}")
async def stop_monitoring(camera_id: int):
    if camera_id in monitoring_flags:
        monitoring_flags[camera_id] = False  # Clear the flag
        return JSONResponse(content={"message": f"Stopped monitoring camera {camera_id}"})
    else:
        return JSONResponse(content={"message": f"No monitoring process found for camera {camera_id}"})

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

@routes.websocket("/ws/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: int):
    await websocket.accept()
    
    if camera_id not in frames:
        await websocket.close()
        return
    
    try:
        while True:
            with frame_locks[camera_id]:
                frame = frames[camera_id]
            if frame is not None:
                # Send frame over WebSocket
                # (Assuming you have a method to encode the frame)
                to_send = resize_and_encode_frame(frame)
                await websocket.send_text(to_send)
            else:
                await asyncio.sleep(0.01)
    except WebSocketDisconnect:
        await websocket.close()
    
# Initialize camera and start capturing frames in a separate thread
def start_camera(camera_id):
    cap = cv2.VideoCapture(camera_id)
    settings = load_settings_from_file()

    while True:
        ret, frame = cap.read()
        if ret:
            if settings.NightVisionEnabled:
                frame = apply_night_vision(frame)
            if settings.FacialRecognitionEnabled:
                frame = detect_faces(frame)
            with frame_locks[camera_id]:
                frames[camera_id] = frame
        else:
            print("Failed to capture frame")