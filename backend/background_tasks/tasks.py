import cv2
import os
from datetime import datetime
import numpy as np
import time
from collections import deque

# Globals
cooldown_period = 300
last_notification_time = 0

frames = {}
frame_locks = {}
monitoring_flags = {}

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
# Initialize variables
label_counter = 0

# Check if the directory exists
for root, dirs, files in os.walk(image_dir):
    for file in files:
        if file.endswith("png") or file.endswith("jpg"):
            path = os.path.join(root, file)
            label = os.path.basename(root)  # Check if this is correct

            # Assign a unique integer to each label
            if label not in label_to_int:
                label_to_int[label] = label_counter
                label_counter += 1

            image = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            faces = face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
            
            for (x, y, w, h) in faces:
                roi = image[y:y+h, x:x+w]
                X_train.append(roi)
                y_labels.append(label)  
                int_labels.append(label_to_int[label])  # Add the corresponding integer label

print(f"Number of training images: {len(X_train)}")
print(f"Number of labels: {len(int_labels)}")
print(f"Label to Int Mapping: {label_to_int}")

# Train the recognizer
if len(X_train) > 0 and len(int_labels) > 0:
    recognizer.train(X_train, np.array(int_labels))
    recognizer.save("face-trainer.yml")
else:
    print("Insufficient data for training.")

int_to_label = {v: k for k, v in label_to_int.items()}  # Inverse mapping

def start_camera(camera_id, settings):
    cap = cv2.VideoCapture(camera_id)

    # Get the frame rate dynamically
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
  
    # Initialize deque with maxlen set to frame_rate * 30
    frames[camera_id] = deque(maxlen=frame_rate * 30)

    while True:
        ret, frame = cap.read()
        if ret:
            if settings.NightVisionEnabled:
                frame = apply_night_vision(frame)
            if settings.FacialRecognitionEnabled:
                frame = detect_faces(frame)
            with frame_locks[camera_id]:
                frames[camera_id].append(frame)
        else:
            # Something went wrong, notify the user
            print("Failed to capture frame")

async def perform_detection(frame, face_cascade, frame_count, skip_frames):
    if frame_count % skip_frames == 0:
        try:
            # Perform face detection
            final_frame = detect_faces(frame, face_cascade)
        except Exception as e:
            print(f"Face detection failed: {e}")
            final_frame = frame  # use the original frame if face detection fails
            
        return final_frame
    return frame

def resize_and_encode_frame(frame):
    original_height, original_width = frame.shape[:2]
    aspect_ratio = original_width / original_height
    new_width = 640  # or any value you want
    new_height = int(new_width / aspect_ratio)
    resized_frame = cv2.resize(frame, (new_width, new_height))
    _, buffer = cv2.imencode('.jpg', resized_frame)
    return buffer.tobytes()

def detect_faces(frame):
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