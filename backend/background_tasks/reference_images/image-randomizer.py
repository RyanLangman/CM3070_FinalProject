import cv2
import numpy as np
from PIL import Image, ImageEnhance
import os

# Create a folder to save augmented images
os.makedirs("augmented_images", exist_ok=True)

def add_noise(image):
    row, col, ch = image.shape
    noise = np.random.randn(row, col, ch)
    noise = noise * 25
    noisy_image = image + noise
    return np.clip(noisy_image, 0, 255).astype(np.uint8)

def rotate_image(image, angle):
    center = tuple(np.array(image.shape[1::-1]) / 2)
    rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)

for image_file in os.listdir("./images"):
    if not image_file.endswith(".jpg"):
        continue

    # Read image
    image_path = os.path.join("./images", image_file)
    image = cv2.imread(image_path)

    # Reduce quality
    for quality in [80, 60, 40, 20]:
        save_path = os.path.join("augmented_images", f"{image_file.split('.')[0]}_quality_{quality}.jpg")
        cv2.imwrite(save_path, image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

    # Resize image while maintaining aspect ratio
    h, w, _ = image.shape
    for scale in [0.8, 0.6, 0.4, 0.2]:
        new_dim = (int(w * scale), int(h * scale))
        resized_image = cv2.resize(image, new_dim, interpolation=cv2.INTER_AREA)
        save_path = os.path.join("augmented_images", f"{image_file.split('.')[0]}_scale_{int(scale*100)}.jpg")
        cv2.imwrite(save_path, resized_image)

    # Rotate image
    for angle in [30, 60, 90, 120]:
        rotated_image = rotate_image(image, angle)
        save_path = os.path.join("augmented_images", f"{image_file.split('.')[0]}_rotated_{angle}.jpg")
        cv2.imwrite(save_path, rotated_image)

    # Add noise
    noisy_image = add_noise(image)
    save_path = os.path.join("augmented_images", f"{image_file.split('.')[0]}_noisy.jpg")
    cv2.imwrite(save_path, noisy_image)

    # Using PIL for more transformations
    pil_image = Image.open(image_path)

    # Adjust brightness
    enhancer = ImageEnhance.Brightness(pil_image)
    brighter_image = enhancer.enhance(1.8)  # 1.0 means no change
    brighter_image.save(os.path.join("augmented_images", f"{image_file.split('.')[0]}_brighter.jpg"))

    # Adjust contrast
    enhancer = ImageEnhance.Contrast(pil_image)
    contrast_image = enhancer.enhance(0.5)  # 1.0 means no change
    contrast_image.save(os.path.join("augmented_images", f"{image_file.split('.')[0]}_contrast.jpg"))