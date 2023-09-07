from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import cv2
import base64
import numpy as np

routes = APIRouter()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

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

    # Initialize YOLO
    net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")

    try:
        while True:
            if connection_closed:
                break

            # Capture frame-by-frame
            ret, frame = cap.read()

            # Perform face detection
            frame_with_faces = detect_faces(frame, face_cascade)

            # Perform object detection
            final_frame = detect_objects(frame_with_faces, net)

            # Resize and encode the frame
            to_send = resize_and_encode_frame(final_frame)

            # Send the frame data as a base64 encoded string
            await websocket.send_text(base64.b64encode(to_send).decode('utf-8'))
    except WebSocketDisconnect:
        connection_closed = True
        cap.release()
        print("WebSocket disconnected, webcam released")
        await websocket.close()

# Helper function for resizing and encoding frames
def resize_and_encode_frame(frame):
    original_height, original_width = frame.shape[:2]
    aspect_ratio = original_width / original_height
    new_width = 640  # or any value you want
    new_height = int(new_width / aspect_ratio)
    resized_frame = cv2.resize(frame, (new_width, new_height))
    _, buffer = cv2.imencode('.jpg', resized_frame)
    return buffer.tobytes()

# Helper function for detecting faces
def detect_faces(frame, face_cascade):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
    return frame

def detect_objects(frame, net):
    # YOLO requires the input frame to be in the shape (416, 416) and normalized
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)

    # Forward pass
    layer_names = net.getLayerNames()
    output_layer_names = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    outputs = net.forward(output_layer_names)

    boxes = []
    confidences = []
    class_ids = []

    # Thresholds for YOLO
    conf_threshold = 0.5
    nms_threshold = 0.4

    h, w = frame.shape[:2]

    for output in outputs:
        for detection in output:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > conf_threshold:
                box = detection[:4] * np.array([w, h, w, h])
                (center_x, center_y, width, height) = box.astype("int")
                x = int(center_x - (width / 2))
                y = int(center_y - (height / 2))

                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Apply non-maxima suppression to suppress weak, overlapping bounding boxes
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    # Draw the bounding box on the frame
    for i in indices:
        i = i[0]
        box = boxes[i]
        (x, y) = (box[0], box[1])
        (w, h) = (box[2], box[3])
        color = [0, 0, 255]  # Red color for generic objects
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

    return frame
