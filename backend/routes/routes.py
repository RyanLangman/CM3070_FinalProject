import os
from typing import List
from websockets.exceptions import ConnectionClosedOK
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import cv2
import base64
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from background_tasks.tasks import resize_and_encode_frame, frames, frame_locks, monitoring_flags, start_camera
from models.config import Config
from models.models import CameraPreview, Previews, Settings, Recording
from helpers.settings_methods import load_settings_from_file, save_settings_to_file
import asyncio
import threading

routes = APIRouter()

@routes.get("/video_feed_previews", response_model=Previews)
async def get_video_feed():
    """
    Retrieve camera previews and return them as a list.
    """
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
    """
    Start monitoring the specified camera if not already monitoring.
    """
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
    """
    Stop monitoring the specified camera if it's being monitored.
    """
    if camera_id in monitoring_flags:
        monitoring_flags[camera_id] = False  # Clear the flag
        return JSONResponse(content={"message": f"Stopped monitoring camera {camera_id}"})
    else:
        return JSONResponse(content={"message": f"No monitoring process found for camera {camera_id}"})

@routes.get("/settings")
async def get_system_settings():
    """
    Get the current system settings.
    """
    current_settings = load_settings_from_file()
    return current_settings

@routes.post("/settings")
async def update_system_settings(settings: Settings):
    """
    Update the system settings.
    """
    save_settings_to_file(settings)
    return {"message": "Settings updated"}

@routes.post("/toggle_facial_recognition")
async def toggle_facial_recognition():
    """
    Toggle facial recognition in system settings.
    """
    settings = load_settings_from_file()
    settings.FacialRecognitionEnabled = not settings.FacialRecognitionEnabled
    save_settings_to_file(settings)
    return {"message": "Facial recognition toggled", "new_state": settings.FacialRecognitionEnabled}

@routes.post("/toggle_night_vision")
async def toggle_night_vision():
    """
    Toggle night vision in system settings.
    """
    settings = load_settings_from_file()
    settings.NightVisionEnabled = not settings.NightVisionEnabled
    save_settings_to_file(settings)
    return {"message": "Night vision toggled", "new_state": settings.NightVisionEnabled}

@routes.get("/recordings")
async def get_recordings():
    """
    List and retrieve recorded video files.
    """
    root_dir = "recordings"
    recordings = []

    if os.path.exists(root_dir):
        for date_folder in sorted(os.listdir(root_dir), reverse=True):
            date_path = os.path.join(root_dir, date_folder)
            if os.path.isdir(date_path):
                for file in sorted(os.listdir(date_path), reverse=True):
                    if file.endswith(".mp4"):
                        recording = Recording(datetime=date_folder, filename=file)
                        recordings.append(recording.dict())

    return JSONResponse(content={"files": recordings})

@routes.delete("/recordings/{date}/{filename}")
async def delete_recording(date: str, filename: str):
    """
    Delete a specific recorded video file based on its date and filename.
    """
    root_dir = "recordings"
    file_path = os.path.join(root_dir, date, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return JSONResponse(content={"message": "Recording successfully deleted."}, status_code=200)
        except Exception as e:
            return JSONResponse(content={"message": f"An error occurred while deleting the recording: {str(e)}"}, status_code=500)
    else:
        raise HTTPException(status_code=404, detail="Recording not found")


@routes.get("/stream")
async def stream_video(datetime: str, filename: str):
    """
    Stream video files based on the provided date and filename.
    """
    relative_video_path = f"recordings/{datetime}/{filename}"
    
    absolute_video_path = os.path.abspath(relative_video_path)
    
    if not os.path.exists(absolute_video_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(absolute_video_path)

@routes.websocket("/ws/{camera_id}")
async def websocket_endpoint(websocket: WebSocket, camera_id: int):
    """
    WebSocket endpoint for real-time video streaming from a camera.
    """
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
    """
    WebSocket endpoint for camera preview streaming.
    """
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
        pass
    finally:
        cap.release() 
        await websocket.close()