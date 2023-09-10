import cv2
import os
from datetime import datetime
import numpy as np
import time

# Globals
cooldown_period = 300
last_notification_time = 0

# Train the face recognizer
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

X_train = []  # Store the face images
y_labels = []  # Store the corresponding labels

# Mapping for label to integer
label_to_int = {}
int_labels = []

base_dir = os.path.dirname(os.path.abspath(__file__))
image_dir = os.path.join(base_dir, "reference_images")
print(f"Scanning directory: {image_dir}")

# Check if the directory exists
for root, dirs, files in os.walk(image_dir):
    for file in files:
        if file.endswith("png") or file.endswith("jpg"):
            path = os.path.join(root, file)
            label = os.path.basename(root)  # Check if this is correct
            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            faces = face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
            
            for (x, y, w, h) in faces:
                roi = image[y:y+h, x:x+w]
                X_train.append(roi)
                y_labels.append(label)  # Check if this line is being executed
else:
    print(f"Directory {image_dir} does not exist.")

print(f"Number of training images: {len(X_train)}")
print(f"Number of labels: {len(int_labels)}")

# Train the recognizer
if len(X_train) > 0 and len(int_labels) > 0:
    recognizer.train(X_train, np.array(int_labels))
    recognizer.save("face-trainer.yml")
else:
    print("Insufficient data for training.")

int_to_label = {v: k for k, v in label_to_int.items()}  # Inverse mapping

async def perform_detection(frame, net, face_cascade, frame_count, skip_frames):
    return detect_faces(frame, face_cascade, recognizer)
    
    # if frame_count % skip_frames == 0:
    #     try:
    #         # Perform face detection
    #         final_frame = detect_faces(frame, face_cascade)
    #     except Exception as e:
    #         print(f"Face detection failed: {e}")
    #         final_frame = frame  # use the original frame if face detection fails
        
    #     # try:
    #     #     # Perform object detection
    #     #     final_frame = detect_objects(final_frame, net)
    #     # except Exception as e:
    #     #     print(f"Object detection failed: {e}")
    #     #     final_frame = final_frame  # use the frame_with_faces if object detection fails
            
    #     return final_frame
    # return frame

def resize_and_encode_frame(frame):
    original_height, original_width = frame.shape[:2]
    aspect_ratio = original_width / original_height
    new_width = 640  # or any value you want
    new_height = int(new_width / aspect_ratio)
    resized_frame = cv2.resize(frame, (new_width, new_height))
    _, buffer = cv2.imencode('.jpg', resized_frame)
    return buffer.tobytes()

def detect_faces(frame, face_cascade):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    
    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        id_, conf = recognizer.predict(roi_gray)

        if id_ < len(y_labels):
            print(f"id_: {id_}, conf: {conf}")

            if conf >= 85:
                label = y_labels[id_]
                cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            else:
                label = "Intruder"
                cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
        else:
            print(f"Warning: id_ {id_} out of range for y_labels {y_labels}")
        
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    return frame

def detect_objects(frame, net, labels):
    labeled_frame = frame.copy()  # To keep a copy with bounding boxes and labels
    # YOLO requires the input frame to be in the shape (416, 416) and normalized
    blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)

    # Forward pass
    layer_names = net.getLayerNames()

    output_layer_names = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]
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
        if isinstance(i, np.ndarray) or isinstance(i, list):
            i = i[0]
        box = boxes[i]
        (x, y) = (box[0], box[1])
        (w, h) = (box[2], box[3])
        
        # Only detect specific objects (pets and dangerous objects)
        detected_class = labels[class_ids[i]]
        if detected_class in ['dog', 'cat', 'bird', 'knife', 'gun']:
            color = [0, 0, 255]  # Red color for these specific objects
            cv2.rectangle(labeled_frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(labeled_frame, detected_class, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
            
            # Save frames
            save_frame(frame, labeled_frame)
            
    return labeled_frame

def send_telegram_notification(message: str):
    # Your Telegram API logic here to send a message
    pass

def save_frame(frame, labeled_frame, folder_name="object_detection"):
    global last_notification_time

    # Create folder if not exists
    current_date = datetime.now().strftime('%Y-%m-%d')
    save_path = os.path.join(folder_name, current_date)
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    # Generate the filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    labeled_filename = os.path.join(save_path, f"{timestamp}_labeled.jpg")
    unlabeled_filename = os.path.join(save_path, f"{timestamp}_unlabeled.jpg")

    # Save the frames
    cv2.imwrite(labeled_filename, labeled_frame)
    cv2.imwrite(unlabeled_filename, frame)

    # Check if enough time has passed since the last notification
    current_time = time.time()
    if current_time - last_notification_time > cooldown_period:
        # Send notification to Telegram
        send_telegram_notification(f"Warning: Dangerous object detected. Check images at {save_path}.")
        
        # Update the last notification time
        last_notification_time = current_time
        
def is_dark_image(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    return mean_brightness < 60  # Adjust the threshold according to your needs

def apply_night_vision(frame):
    if is_dark_image(frame):
        # Convert the image to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization
        equalized_gray = cv2.equalizeHist(gray)
        
        # Convert single channel to 3 channels
        return cv2.cvtColor(equalized_gray, cv2.COLOR_GRAY2BGR)
    
    return frame