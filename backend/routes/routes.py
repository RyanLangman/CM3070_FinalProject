from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import base64
import numpy as np

routes = APIRouter()

@routes.get("/video_feed")
async def get_video_feed():
    return {"message": "Video feed will be returned here"}

@routes.get("/settings")
async def get_system_settings():
    return {"message": "System settings will be returned here"}

@routes.post("/toggle_object_detection")
async def toggle_object_detection():
    return {"message": "Object detection toggled"}

@routes.post("/toggle_facial_recognition")
async def toggle_facial_recognition():
    return {"message": "Facial recognition toggled"}

@routes.post("/toggle_fall_detection")
async def toggle_fall_detection():
    return {"message": "Fall detection toggled"}

@routes.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    cap = cv2.VideoCapture(0)  # 0 is the ID for the default webcam
    connection_closed = False

    try:
        while True:
            if connection_closed:
                break

            ret, frame = cap.read()
            if not ret:
                print("Failed to capture image")
                break

            # Mock machine learning processing: Draw a simple rectangle
            cv2.rectangle(frame, (50, 50), (150, 150), (0, 255, 0), 2)

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Send as base64 to reduce data size
            await websocket.send_text(base64.b64encode(frame).decode('utf-8'))
    except WebSocketDisconnect:
        connection_closed = True
        cap.release()
        print("WebSocket disconnected, webcam released")
        await websocket.close()