import os
import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
from config import Config
from database.db import query_one, execute_sql, transaction
from face_atm.face_detector import FaceDetector
from face_atm.security_service import generate_salt, hash_pin, log_security_event
from face_atm.anti_spoofing import BiometricAntiSpoofing

class LBPHFaceManager:
    def __init__(self):
        self.detector = FaceDetector()
        Config.FACE_SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
        Config.FACE_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    def create_recognizer(self):
        """
        Creates OpenCV LBPH Face Recognizer with tuned parameters for higher accuracy.
        """
        return cv2.face.LBPHFaceRecognizer_create(
            radius=2,        # Increased radius for capturing larger patterns
            neighbors=12,    # Increased neighbors for finer granularity
            grid_x=10,       # Higher grid_x for better spatial resolution
            grid_y=10        # Higher grid_y for better spatial resolution
        )

    def get_model_path(self, account_number: str) -> Path:
        return Config.FACE_MODELS_DIR / f"user_{account_number}.yml"

    def get_samples_dir(self, account_number: str) -> Path:
        p = Config.FACE_SAMPLES_DIR / account_number
        p.mkdir(parents=True, exist_ok=True)
        return p

    def save_face_samples(self, account_number: str, images_or_frames: list):
        """
        Processes and saves normalized 200x200 face samples to disk.
        """
        sample_dir = self.get_samples_dir(account_number)
        saved_count = 0
        
        for idx, img in enumerate(images_or_frames):
            faces = self.detector.detect_faces(img)
            if len(faces) == 0:
                continue
            # Pick largest face
            largest_face = max(faces, key=lambda b: b[2] * b[3])
            preprocessed = self.detector.preprocess_face(img, largest_face)
            if preprocessed is not None:
                filename = sample_dir / f"sample_{idx:03d}.jpg"
                cv2.imwrite(str(filename), preprocessed)
                saved_count += 1
                
        return saved_count

    def train_user_model(self, account_number: str):
        """
        Trains LBPH model using all saved face samples for the account.
        Saves trained model to YAML.
        """
        sample_dir = self.get_samples_dir(account_number)
        sample_files = list(sample_dir.glob("*.jpg")) + list(sample_dir.glob("*.png"))
        
        if len(sample_files) < 5:
            return False, f"Insufficient samples ({len(sample_files)}). Need at least 5 face samples to train.", 0

        faces = []
        labels = []
        
        # Label integer 1 for this account
        for f in sample_files:
            img = cv2.imread(str(f), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                resized = cv2.resize(img, (200, 200))
                faces.append(resized)
                labels.append(1)

        recognizer = self.create_recognizer()
        recognizer.train(faces, np.array(labels))
        
        model_path = self.get_model_path(account_number)
        recognizer.write(str(model_path))
        
        # Update face_models in database
        execute_sql(
            """
            INSERT INTO face_models (account_number, model_path, sample_count, confidence_threshold, status)
            VALUES (?, ?, ?, ?, 'ACTIVE')
            ON CONFLICT(account_number) DO UPDATE SET
                model_path = excluded.model_path,
                sample_count = excluded.sample_count,
                trained_at = CURRENT_TIMESTAMP,
                status = 'ACTIVE'
            """,
            (account_number, str(model_path), len(faces), Config.LBPH_CONFIDENCE_THRESHOLD)
        )
        
        log_security_event(account_number, "MODEL_TRAINED", f"Trained LBPH model on {len(faces)} face samples.")
        return True, f"Successfully trained face model on {len(faces)} samples.", len(faces)

    def load_model(self, account_number: str):
        model_path = self.get_model_path(account_number)
        if not model_path.exists():
            sample_dir = self.get_samples_dir(account_number)
            if len(list(sample_dir.glob("*.jpg"))) >= 5:
                self.train_user_model(account_number)
        if not model_path.exists():
            return None
        recognizer = self.create_recognizer()
        recognizer.read(str(model_path))
        return recognizer

    def verify_frame(self, account_number: str, frame):
        """
        Processes a single frame for live verification.
        Returns:
            dict with:
                success (bool),
                face_detected (bool),
                distance (float),
                confidence_score (float), # 0-100%
                threshold (float),
                message (str),
                bbox (tuple)
        """
        faces = self.detector.detect_faces(frame)
        if len(faces) == 0:
            return {
                "success": False,
                "face_detected": False,
                "distance": 999.0,
                "confidence_score": 0.0,
                "threshold": Config.LBPH_CONFIDENCE_THRESHOLD,
                "message": "No face detected in camera viewport.",
                "bbox": None
            }

        # Pick largest detected face
        largest_face = max(faces, key=lambda b: b[2] * b[3])
        preprocessed = self.detector.preprocess_face(frame, largest_face)
        if preprocessed is None:
            return {
                "success": False,
                "face_detected": False,
                "distance": 999.0,
                "confidence_score": 0.0,
                "threshold": Config.LBPH_CONFIDENCE_THRESHOLD,
                "message": "Could not extract face region.",
                "bbox": None
            }

        recognizer = self.load_model(account_number)
        if not recognizer:
            return {
                "success": False,
                "face_detected": True,
                "distance": 999.0,
                "confidence_score": 0.0,
                "threshold": Config.LBPH_CONFIDENCE_THRESHOLD,
                "message": f"Biometric model not found for {account_number}. Please register your face first.",
                "bbox": [int(v) for v in largest_face]
            }

        # Evaluate biometric liveness on face bounding box
        (fx, fy, fw, fh) = [int(v) for v in largest_face]
        face_crop = frame[fy:fy+fh, fx:fx+fw] if (frame is not None and len(frame.shape) >= 2) else None
        liveness_info = BiometricAntiSpoofing.evaluate_liveness(frame, face_crop)

        label, distance = recognizer.predict(preprocessed)
        
        # Lower distance in LBPH means closer match
        # Distance under threshold is authentic
        threshold = Config.LBPH_CONFIDENCE_THRESHOLD
        is_match = (distance <= threshold)
        
        # Estimate match confidence percentage
        match_confidence = max(0.0, min(100.0, (1.0 - (distance / 120.0)) * 100.0))

        # Overall verification message
        if is_match and not liveness_info["is_live"]:
            status_msg = f"Face matched but anti-spoofing alert: {', '.join(liveness_info['reasons'])}"
        elif is_match:
            status_msg = "Face match and liveness verified."
        else:
            status_msg = "Face verification failed (confidence below threshold)."

        return {
            "success": is_match,
            "face_detected": True,
            "distance": round(float(distance), 2),
            "confidence_score": round(match_confidence, 1),
            "threshold": threshold,
            "message": status_msg,
            "bbox": [int(v) for v in largest_face],
            "liveness": liveness_info
        }

    def register_user(self, account_number: str, full_name: str, email: str, pin: str, initial_balance: float = 1500.0):
        """
        Creates user account in database with PBKDF2 hashed PIN.
        """
        existing = query_one("SELECT account_number FROM users WHERE account_number = ?", (account_number,))
        if existing:
            return False, f"Account number '{account_number}' already exists."

        salt = generate_salt()
        hashed = hash_pin(pin, salt)

        with transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (account_number, full_name, email, pin_hash, pin_salt)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account_number, full_name, email, hashed, salt)
            )
            cursor.execute(
                """
                INSERT INTO accounts (account_number, balance, account_type, daily_limit)
                VALUES (?, ?, 'SAVINGS', 5000.0)
                """,
                (account_number, initial_balance)
            )
            cursor.execute(
                """
                INSERT INTO transactions (account_number, type, amount, balance_after, description)
                VALUES (?, 'DEPOSIT', ?, ?, 'Initial Account Opening Balance')
                """,
                (account_number, initial_balance, initial_balance)
            )

        log_security_event(account_number, "USER_REGISTERED", f"Created account for {full_name} with balance ${initial_balance:,.2f}")
        return True, "User registered successfully. Proceed to face capture."
