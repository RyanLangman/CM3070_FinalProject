import base64
from copy import deepcopy
import threading
import cv2
import os
from datetime import datetime, timedelta
import numpy as np
import time
from collections import deque
from queue import Queue
from helpers.email import send_email

from helpers.settings_methods import load_settings_from_file

# Globals
settings = load_settings_from_file('settings.json')
video_write_queue = Queue()
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

# Global video writing queue
video_write_queue = Queue()

def video_writer():
    """
    Thread function for writing video frames to video files.
    """
    while True:
        task = video_write_queue.get()

        if task is None:
            # Sentinel value to stop the thread
            break

        fourcc, frames_to_save, folder_path, camera_id, frame_rate, height, width = task

        # Generate a new timestamp for each file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out = cv2.VideoWriter(f"{folder_path}/{camera_id}_{timestamp}.mp4", fourcc, frame_rate, (width, height))

        for f in frames_to_save:
            out.write(f)
        
        out.release()

        video_write_queue.task_done()

def start_camera(camera_id, settings):    
    """
    Start capturing video from a camera and processing it.
    
    Args:
        camera_id (int): ID of the camera to capture from.
        settings: Settings object containing system settings.
    """
    video_writer_thread = threading.Thread(target=video_writer)
    video_writer_thread.start()

    cap = cv2.VideoCapture(camera_id)
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))

    frames_to_save = deque(maxlen=frame_rate * (60))

    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    height = None
    width = None
    
    # Testing
    last_frame_to_email = None

    while monitoring_flags.get(camera_id, True):
        ret, frame = cap.read()
        if ret:
            if settings.FacialRecognitionEnabled:
                detect_faces(frame)
            if settings.NightVisionEnabled:
                frame = apply_night_vision(frame)

            # Initialize video writer object after we get the first frame
            if height is None and width is None:
                height, width = frame.shape[:2]
                date_folder = datetime.now().strftime('%Y-%m-%d')
                folder_path = f"recordings/{date_folder}"
                os.makedirs(folder_path, exist_ok=True)

            frames_to_save.append(frame)
            last_frame_to_email = frame

            if len(frames_to_save) == frames_to_save.maxlen:
                video_write_queue.put((fourcc, deepcopy(frames_to_save), folder_path, camera_id, frame_rate, height, width))
                frames_to_save.clear()

            with frame_locks[camera_id]:
                frames[camera_id] = frame
        else:
            print("Failed to capture frame")

    video_write_queue.put((fourcc, deepcopy(frames_to_save), folder_path, camera_id, frame_rate, height, width))
    frames_to_save.clear()

    cap.release()
    frames.pop(camera_id, None)
    frame_locks.pop(camera_id, None)
    
    video_write_queue.put(None)
    video_writer_thread.join()

async def perform_detection(frame, face_cascade, frame_count, skip_frames):
    """
    Perform face detection on the given frame.

    Args:
        frame: The frame to perform face detection on.
        face_cascade: The face cascade classifier.
        frame_count: The current frame count.
        skip_frames: The number of frames to skip before performing detection.

    Returns:
        The frame with face detection annotations.
    """
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
    """
    Resize and encode a frame for streaming.

    Args:
        frame: The frame to resize and encode.

    Returns:
        bytes: The encoded frame.
    """
    original_height, original_width = frame.shape[:2]
    aspect_ratio = original_width / original_height
    new_width = 640  # or any value you want
    new_height = int(new_width / aspect_ratio)
    resized_frame = cv2.resize(frame, (new_width, new_height))
    _, buffer = cv2.imencode('.jpg', resized_frame)
    return buffer.tobytes()

def resize_for_prediction(frame, target_height=480, target_width=640):
    """
    Resize a frame for face recognition prediction.

    Args:
        frame: The frame to resize.
        target_height (int): The target height after resizing.
        target_width (int): The target width after resizing.

    Returns:
        np.ndarray: The resized frame.
    """
    height, width = frame.shape[:2]
    
    # Calculate the ratio of the new dimensions to the original dimensions
    height_ratio = target_height / height
    width_ratio = target_width / width
    
    # Use the ratio to resize the frame
    new_dim = (int(width * width_ratio), int(height * height_ratio))
    resized_frame = cv2.resize(frame, new_dim, interpolation=cv2.INTER_AREA)
    
    return resized_frame

def detect_faces(frame):
    """
    Detect faces in the given frame and annotate it.

    Args:
        frame: The frame to detect faces in.

    Returns:
        np.ndarray: The annotated frame.
    """
    global last_saved_time
    current_time = datetime.now()

    # Keep an unaltered copy of the frame
    copied_frame = frame.copy()
    resized_frame = resize_for_prediction(frame)
    gray_resized = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_resized, scaleFactor=1.1, minNeighbors=5)

    height_ratio = frame.shape[0] / resized_frame.shape[0]
    width_ratio = frame.shape[1] / resized_frame.shape[1]

    for (x, y, w, h) in faces:
        x, y, w, h = int(x * width_ratio), int(y * height_ratio), int(w * width_ratio), int(h * height_ratio)
        
        roi_gray = gray_resized[y:y+h, x:x+w]
        id_, conf = recognizer.predict(roi_gray)

        if id_ < len(y_labels):
            if conf >= 95:
                label = y_labels[id_]
                cv2.putText(copied_frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            else:
                label = "Intruder"
                cv2.putText(copied_frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

                if last_saved_time is None or current_time - last_saved_time >= timedelta(seconds=15):      
                    cv2.rectangle(copied_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    save_frame(frame, copied_frame)

                    last_saved_time = current_time
        else:
            print(f"Warning: id_ {id_} out of range for y_labels {y_labels}")

    return copied_frame

def save_frame(frame, labeled_frame, folder_name="notifications"):
    """
    Save frames with labels and handle notification.

    Args:
        frame: The frame to save.
        labeled_frame: The labeled frame.
        folder_name (str): The folder name to save frames.
    """
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
        _, buffer = cv2.imencode('.jpg', labeled_frame)
        image_data = buffer.tobytes()
        send_email(image_data)
        
        # Update the last notification time
        last_notification_time = current_time
        
def is_dark_image(frame):
    """
    Check if an image is dark based on its mean brightness.

    Args:
        frame: The image frame to check.

    Returns:
        bool: True if the image is dark, False otherwise.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    return mean_brightness < 30  # Adjust the threshold according to your needs

def apply_night_vision(frame):
    """
    Apply night vision enhancement to a frame if it's dark.

    Args:
        frame: The frame to enhance.

    Returns:
        np.ndarray: The enhanced frame.
    """
    if is_dark_image(frame):
        # Convert to YUV color space
        yuv = cv2.cvtColor(frame, cv2.COLOR_BGR2YUV)
        
        # Apply Adaptive Histogram Equalization to the Y channel
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        yuv[:,:,0] = clahe.apply(yuv[:,:,0])
        
        # Convert back to BGR color space
        enhanced_bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)
        
        return enhanced_bgr
    
    return frame