import os
from typing import List
from websockets.exceptions import ConnectionClosedOK
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import base64
from fastapi.responses import JSONResponse, StreamingResponse
from background_tasks.tasks import resize_and_encode_frame, frames, frame_locks, monitoring_flags, start_camera
from models.config import Config
from models.models import CameraPreview, Previews, Settings, Recording
from helpers.settings_methods import load_settings_from_file, save_settings_to_file
import asyncio
import threading

routes = APIRouter()

@routes.get("/video_feed_previews", response_model=Previews)
async def get_video_feed():
    available_cameras = Config.available_cameras
    camera_previews: List[CameraPreview] = []
    
    for camera_id in available_cameras:
        cap = cv2.VideoCapture(camera_id)
        ret, frame = cap.read()

        if ret:
            to_send = resize_and_encode_frame(frame)
            encoded_frame = base64.b64encode(to_send).decode('utf-8')
        else:
            encoded_frame = None

        is_monitoring = monitoring_flags.get(camera_id, False)
        
        cap.release()

        if encoded_frame is not None:
            preview = CameraPreview(
                cameraId=camera_id,
                frame=encoded_frame,
                isMonitoring=is_monitoring
            )
            camera_previews.append(preview)

    return Previews(cameraPreviews=camera_previews)

@routes.post("/start_monitoring/{camera_id}")
async def start_monitoring(camera_id: int):
    if camera_id not in frames:
        frames[camera_id] = None
        frame_locks[camera_id] = threading.Lock()
        monitoring_flags[camera_id] = True  # Set the flag
        current_settings = load_settings_from_file()
        threading.Thread(target=start_camera, args=(camera_id, current_settings)).start()
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
    root_dir = "recordings"  # Replace this with the actual path to your 'recordings' directory
    recordings = []

    if os.path.exists(root_dir):
        for date_folder in sorted(os.listdir(root_dir), reverse=True):  # Sort folders by datetime in descending order
            date_path = os.path.join(root_dir, date_folder)
            if os.path.isdir(date_path):
                for file in sorted(os.listdir(date_path), reverse=True):  # Sort files by filename in descending order
                    if file.endswith(".mp4"):  # Include other video extensions if necessary
                        recording = Recording(datetime=date_folder, filename=file)
                        recordings.append(recording.dict())

    return JSONResponse(content={"files": recordings})

@routes.get("/stream")
async def stream_video(datetime: str, filename: str):
    video_path = f"recordings/{datetime}/{filename}"

    if not os.path.exists(video_path):
        return {"status": 404, "detail": "File not found"}

    def iterfile(): 
        with open(video_path, mode="rb") as file_like:  # 
            yield from file_like  # 

    return StreamingResponse(iterfile(), media_type="video/mp4")

@routes.websocket("/ws/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: int):
    await websocket.accept()

    if camera_id not in frames:
        await websocket.close()
        return

    try:
        while True:
            with frame_locks[camera_id]:
                if frames[camera_id] is not None and len(frames[camera_id]) > 0:
                    frame = frames[camera_id]  # Get the latest frame
                else:
                    frame = None

            if frame is not None:
                to_send = resize_and_encode_frame(frame)
                await asyncio.sleep(0.05)
                await websocket.send_text(base64.b64encode(to_send).decode('utf-8'))
            else:
                await asyncio.sleep(0.05)
    except ConnectionClosedOK:
        print("WebSocket connection closed cleanly.")
    except WebSocketDisconnect:
        await websocket.close()

@routes.websocket("/ws/{camera_id}/preview")
async def websocket_endpoint(websocket: WebSocket, camera_id: int):
    await websocket.accept()

    cap = cv2.VideoCapture(camera_id)

    try:
        while True:
            ret, frame = cap.read()

            if ret:
                to_send = resize_and_encode_frame(frame)
                await asyncio.sleep(0.05)
                await websocket.send_text(base64.b64encode(to_send).decode('utf-8'))
            else:
                await websocket.send_text("error: Failed to capture frame")
    except WebSocketDisconnect:
        pass  # Handle disconnection
    finally:
        cap.release() 
        await websocket.close()