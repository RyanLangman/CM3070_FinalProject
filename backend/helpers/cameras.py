import cv2

def get_available_cameras(max_cameras=10):
    available_cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.read()[0]:
            available_cameras.append(i)
        cap.release()
    return available_cameras