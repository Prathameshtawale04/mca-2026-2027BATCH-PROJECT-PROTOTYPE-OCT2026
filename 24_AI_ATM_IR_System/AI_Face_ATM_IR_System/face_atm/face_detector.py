import cv2
import os
import numpy as np
from pathlib import Path
from config import Config

class FaceDetector:
    def __init__(self):
        # Look for OpenCV bundled cascade first, then config path
        cascade_filename = "haarcascade_frontalface_default.xml"
        bundled_path = os.path.join(cv2.data.haarcascades, cascade_filename)
        
        if os.path.exists(bundled_path):
            self.cascade_path = bundled_path
        elif os.path.exists(Config.HAAR_CASCADE_PATH):
            self.cascade_path = Config.HAAR_CASCADE_PATH
        else:
            raise FileNotFoundError(f"Haar cascade XML not found in {bundled_path} or {Config.HAAR_CASCADE_PATH}")

        self.classifier = cv2.CascadeClassifier(self.cascade_path)
        if self.classifier.empty():
            raise RuntimeError(f"Failed to load Haar Cascade from {self.cascade_path}")

    def detect_faces(self, image, scale_factor=1.1, min_neighbors=5, min_size=(60, 60)):
        """
        Detects faces in BGR or Grayscale image.
        Returns list of (x, y, w, h) bounding boxes.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        faces = self.classifier.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=min_size,
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        return faces

    def preprocess_face(self, image, bbox=None, target_size=(200, 200)):
        """
        Crops, converts to grayscale, resizes, and equalizes histogram for LBPH training/predict.
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        if bbox is not None:
            x, y, w, h = bbox
            # Add small 5% padding if within image bounds
            pad_x = int(w * 0.05)
            pad_y = int(h * 0.05)
            x1 = max(0, x - pad_x)
            y1 = max(0, y - pad_y)
            x2 = min(gray.shape[1], x + w + pad_x)
            y2 = min(gray.shape[0], y + h + pad_y)
            face_roi = gray[y1:y2, x1:x2]
        else:
            face_roi = gray

        if face_roi.size == 0:
            return None

        resized = cv2.resize(face_roi, target_size, interpolation=cv2.INTER_AREA)
        equalized = cv2.equalizeHist(resized)
        return equalized

    def draw_hud(self, frame, faces, label="DETECTED", status_color=(0, 255, 127)):
        """
        Draws high-tech ATM biometric HUD brackets around detected faces.
        """
        output = frame.copy()
        for (x, y, w, h) in faces:
            # Corner line length
            d = int(min(w, h) * 0.25)
            t = 2
            # Bounding box subtle
            cv2.rectangle(output, (x, y), (x + w, y + h), (50, 50, 50), 1)
            # Top-left corner
            cv2.line(output, (x, y), (x + d, y), status_color, t)
            cv2.line(output, (x, y), (x, y + d), status_color, t)
            # Top-right corner
            cv2.line(output, (x + w, y), (x + w - d, y), status_color, t)
            cv2.line(output, (x + w, y), (x + w, y + d), status_color, t)
            # Bottom-left corner
            cv2.line(output, (x, y + h), (x + d, y + h), status_color, t)
            cv2.line(output, (x, y + h), (x, y + h - d), status_color, t)
            # Bottom-right corner
            cv2.line(output, (x + w, y + h), (x + w - d, y + h), status_color, t)
            cv2.line(output, (x + w, y + h), (x + w, y + h - d), status_color, t)
            
            # Label
            cv2.putText(
                output,
                label,
                (x, max(20, y - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                status_color,
                2
            )
        return output
