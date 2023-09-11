import cv2
import os
from datetime import datetime, timedelta
import numpy as np
import time
from collections import deque

# Globals
last_saved_time = None
cooldown_period = 300
last_notification_time = 0

frames = {}
frame_locks = {}
monitoring_flags = {}

# Train the face recognizer
# face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
recognizer = cv2.face.LBPHFaceRecognizer_create()

X_train = []  # Store the face images
y_labels = []  # Store the corresponding labels

# Mapping for label to integer
label_to_int = {}
int_labels = []

base_dir = os.path.dirname(os.path.abspath(__file__))
image_dir = os.path.join(base_dir, "reference_images")
# print(f"Scanning directory: {image_dir}")
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
                int_labels.append(label_to_int[label])

if len(X_train) > 0 and len(int_labels) > 0:
    recognizer.train(X_train, np.array(int_labels))
    recognizer.save("face-trainer.yml")
else:
    print("Insufficient data for training.")

int_to_label = {v: k for k, v in label_to_int.items()}

def start_camera(camera_id, settings):
    cap = cv2.VideoCapture(camera_id)
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))

    # Create deque to store 5 seconds of frames
    frames_to_save = deque(maxlen=frame_rate * 5)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec for .mp4 format
    out = None  # Will be initialized later based on the first frame's shape

    while monitoring_flags.get(camera_id, True):
        ret, frame = cap.read()
        if ret:
            if settings.FacialRecognitionEnabled:
                detect_faces(frame)
            if settings.NightVisionEnabled:
                frame = apply_night_vision(frame)

            # Initialize video writer object after we get the first frame
            if out is None:
                height, width = frame.shape[:2]
                date_folder = datetime.now().strftime('%Y-%m-%d')
                folder_path = f"recordings/{date_folder}"
                os.makedirs(folder_path, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                out = cv2.VideoWriter(f"{folder_path}/{camera_id}_{timestamp}.mp4", fourcc, frame_rate, (width, height))

            frames_to_save.append(frame)

            # If deque is full, write frames to disk and clear the deque
            if len(frames_to_save) == frames_to_save.maxlen:
                for f in frames_to_save:
                    out.write(f)
                frames_to_save.clear()  # Clear the deque for the next set of frames

            with frame_locks[camera_id]:
                frames[camera_id].append(frame)
        else:
            print("Failed to capture frame")

    # Release resources
    cap.release()
    out.release()
    frames.pop(camera_id, None)
    frame_locks.pop(camera_id, None)

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
    global last_saved_time
    current_time = datetime.now()

    # Keep an unaltered copy of the frame
    unaltered_frame = frame.copy()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        id_, conf = recognizer.predict(roi_gray)

        if id_ < len(y_labels):
            # print(f"id_: {id_}, conf: {conf}")

            if conf >= 85:
                label = y_labels[id_]
                cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            else:
                label = "Intruder"
                cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

                if last_saved_time is None or current_time - last_saved_time >= timedelta(seconds=15):
                    # Save the frame when intruder detected
                    date_stamp = current_time.strftime("%Y-%m-%d")
                    time_stamp = current_time.strftime("%H%M%S")
                    folder_path = f"notifications/{date_stamp}"
                    os.makedirs(folder_path, exist_ok=True)

                    labelled_frame_path = os.path.join(folder_path, f"{date_stamp}_{time_stamp}_intruder_labelled.jpg")
                    unlabelled_frame_path = os.path.join(folder_path, f"{date_stamp}_{time_stamp}_intruder_unlabelled.jpg")

                    cv2.imwrite(labelled_frame_path, frame)  # Save frame with label and box
                    cv2.imwrite(unlabelled_frame_path, unaltered_frame)  # Save unaltered frame

                    last_saved_time = current_time  # Update the last saved time
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
    return mean_brightness < 30  # Adjust the threshold according to your needs

def apply_night_vision(frame):
    if is_dark_image(frame):
        # Convert the image to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization
        equalized_gray = cv2.equalizeHist(gray)
        
        # Convert single channel to 3 channels
        return cv2.cvtColor(equalized_gray, cv2.COLOR_GRAY2BGR)
    
    return frame