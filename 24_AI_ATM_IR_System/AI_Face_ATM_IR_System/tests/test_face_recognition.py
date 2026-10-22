import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from face_atm.face_detector import FaceDetector
from face_atm.face_recognizer import LBPHFaceManager

def test_face_detector_initialization():
    detector = FaceDetector()
    assert detector.classifier is not None
    assert not detector.classifier.empty()

def test_preprocess_face():
    detector = FaceDetector()
    dummy_img = np.ones((300, 300, 3), dtype=np.uint8) * 128
    preprocessed = detector.preprocess_face(dummy_img, bbox=(50, 50, 100, 100))
    
    assert preprocessed is not None
    assert preprocessed.shape == (200, 200)

def test_lbph_face_manager():
    manager = LBPHFaceManager()
    model = manager.load_model("ACC1001")
    assert model is not None

def test_verify_frame_matching():
    manager = LBPHFaceManager()
    # Read sample image from account directory
    samples_dir = manager.get_samples_dir("ACC1001")
    sample_files = list(samples_dir.glob("*.jpg"))
    assert len(sample_files) > 0

    import cv2
    sample_img = cv2.imread(str(sample_files[0]))
    # Predict directly on sample
    recognizer = manager.load_model("ACC1001")
    gray = cv2.cvtColor(sample_img, cv2.COLOR_BGR2GRAY)
    label, distance = recognizer.predict(gray)
    
    # Distance should be low on training sample
    assert distance < 50.0
