"""Biometric Computer Vision Service (Haar Face Detection & LBPH Face Recognition)."""

import os
import re
import cv2
import numpy as np
import base64
from pathlib import Path
from flask import current_app
from database.db import query_db, execute_db
from services.auth_service import log_audit_event

def get_cascade():
    """Load OpenCV Haar Cascade classifier for frontal face detection."""
    try:
        cascade_path = current_app.config.get("HAAR_CASCADE_PATH")
    except RuntimeError:
        cascade_path = str(Path(__file__).resolve().parent.parent / "data" / "haarcascade_frontalface_default.xml")
    
    if not os.path.exists(cascade_path):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        raise RuntimeError(f"Failed to load Haar Cascade from: {cascade_path}")
    return cascade

def decode_image_base64(image_data: str) -> np.ndarray:
    """Validate and decode a base64-encoded image string into an OpenCV BGR matrix."""
    if not image_data or not isinstance(image_data, str):
        raise ValueError("Empty or invalid image data payload")

    # Strip data URI header if present (e.g. data:image/jpeg;base64,...)
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]

    raw_bytes = base64.b64decode(image_data)
    nparr = np.frombuffer(raw_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image bytes into valid picture matrix")
    
    if img.shape[0] < 80 or img.shape[1] < 80:
        raise ValueError("Image dimensions too small (minimum 80x80 required)")
        
    return img

def validate_and_extract_face(img_bgr: np.ndarray) -> tuple[bool, str, np.ndarray | None]:
    """
    Detect frontal face using Haar Cascade.
    Enforces single-face constraint and image quality checks.
    Returns: (success: bool, message: str, cropped_face_gray: np.ndarray | None)
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Blurriness check via Laplacian variance
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if lap_var < 15.0:
        return False, f"Image is too blurry (Laplacian variance {lap_var:.1f} < 15.0). Please hold still.", None

    cascade = get_cascade()
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(60, 60)
    )

    if len(faces) == 0:
        return False, "No face detected in frame. Ensure your face is centered and illuminated.", None
    elif len(faces) > 1:
        return False, f"Multiple faces detected ({len(faces)}). Ensure only one person is in the frame.", None

    (x, y, w, h) = faces[0]
    # Crop and normalize face to standard 160x160 resolution
    face_roi = gray[y:y+h, x:x+w]
    face_resized = cv2.resize(face_roi, (160, 160), interpolation=cv2.INTER_AREA)
    
    # Equalize histogram for illumination robustness
    face_eq = cv2.equalizeHist(face_resized)
    return True, "Face successfully detected and cropped.", face_eq

def get_samples_dir(account_number: str) -> Path:
    """Get sample directory path for account."""
    try:
        base = current_app.config["FACE_SAMPLES_DIR"]
    except RuntimeError:
        base = Path(__file__).resolve().parent.parent / "data" / "face_data" / "samples"
    path = Path(base) / account_number
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_models_dir() -> Path:
    """Get directory for trained LBPH models."""
    try:
        base = current_app.config["FACE_MODELS_DIR"]
    except RuntimeError:
        base = Path(__file__).resolve().parent.parent / "data" / "face_data" / "models"
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_face_sample(account_number: str, face_gray: np.ndarray) -> int:
    """Save cropped face sample to disk and return total sample count."""
    samples_dir = get_samples_dir(account_number)
    existing_files = list(samples_dir.glob("sample_*.jpg"))
    next_idx = len(existing_files)
    
    filename = samples_dir / f"sample_{next_idx:03d}.jpg"
    cv2.imwrite(str(filename), face_gray)
    return next_idx + 1

def train_lbph_recognizer(account_number: str) -> tuple[bool, str, dict]:
    """
    Train an LBPH Face Recognizer for a specific user using captured samples.
    Returns: (success: bool, message: str, info_dict: dict)
    """
    samples_dir = get_samples_dir(account_number)
    image_paths = sorted(list(samples_dir.glob("sample_*.jpg")))
    
    if len(image_paths) < 5:
        return False, f"Insufficient samples ({len(image_paths)} found, minimum 5 required for training).", {}

    faces = []
    labels = []
    
    for img_path in image_paths:
        img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if img is not None:
            if img.shape != (160, 160):
                img = cv2.resize(img, (160, 160))
            faces.append(img)
            labels.append(1)  # Target user label

    if len(faces) == 0:
        return False, "Failed to load face images from samples directory.", {}

    # Initialize OpenCV LBPH Recognizer
    # radius=1, neighbors=8, grid_x=8, grid_y=8
    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
    recognizer.train(faces, np.array(labels, dtype=np.int32))

    models_dir = get_models_dir()
    model_path = models_dir / f"user_{account_number}.yml"
    recognizer.write(str(model_path))

    # Update or insert database metadata
    rel_model_path = str(model_path.relative_to(Path(__file__).resolve().parent.parent))
    existing_meta = query_db("SELECT id FROM face_metadata WHERE account_number = ?", (account_number,), one=True)
    if existing_meta:
        execute_db(
            """UPDATE face_metadata 
               SET sample_count = ?, model_path = ?, status = 'ACTIVE', enrolled_at = CURRENT_TIMESTAMP
               WHERE account_number = ?""",
            (len(faces), rel_model_path, account_number)
        )
    else:
        acc = query_db("SELECT user_id FROM accounts WHERE account_number = ?", (account_number,), one=True)
        uid = acc["user_id"] if acc else None
        if uid:
            execute_db(
                """INSERT INTO face_metadata (user_id, account_number, sample_count, model_path, status, enrolled_at)
                   VALUES (?, ?, ?, ?, 'ACTIVE', CURRENT_TIMESTAMP)""",
                (uid, account_number, len(faces), rel_model_path)
            )

    log_audit_event(None, account_number, "TRAIN_FACE_MODEL", f"LBPH model trained with {len(faces)} samples", None, "SUCCESS")

    return True, f"LBPH model successfully trained with {len(faces)} biometric samples.", {
        "samples_count": len(faces),
        "model_file": str(model_path.name),
        "status": "ACTIVE"
    }

def generate_synthetic_samples_for_account(account_number: str, count: int = 15) -> tuple[bool, str, dict]:
    """
    Generate synthetic consented face samples with geometric facial features and realistic noise
    for the specified account number, and train the LBPH model.
    Enables testing and evaluation when physical webcam access is unavailable or denied.
    """
    samples_dir = get_samples_dir(account_number)
    np.random.seed(abs(hash(account_number)) % 100000)
    for i in range(count):
        img = np.zeros((160, 160), dtype=np.uint8)
        # Background subtle gradient
        for y in range(160):
            val = int(np.clip(120 + int((y - 80) * 0.25), 50, 210))
            img[y, :] = val
        # Face ellipse
        cv2.ellipse(img, (80, 80), (48, 64), 0, 0, 360, 180, -1)
        # Eyes
        cv2.circle(img, (62, 65), 7, 50, -1)
        cv2.circle(img, (98, 65), 7, 50, -1)
        # Pupils
        cv2.circle(img, (62, 65), 3, 20, -1)
        cv2.circle(img, (98, 65), 3, 20, -1)
        # Nose
        cv2.line(img, (80, 70), (80, 95), 70, 2)
        # Mouth
        cv2.ellipse(img, (80, 115), (20, 10), 0, 0, 180, 60, 2)
        # Random noise for realistic LBPH texture variation
        noise = np.random.normal(0, 3.5, img.shape).astype(np.int16)
        noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        filename = samples_dir / f"sample_{i:03d}.jpg"
        cv2.imwrite(str(filename), noisy)

    # Train recognizer with the new samples
    ok, msg, details = train_lbph_recognizer(account_number)
    if ok:
        log_audit_event(None, account_number, "GENERATE_SYNTHETIC_FACE", f"Generated {count} synthetic biometric samples and trained model", None, "SUCCESS")
        return True, f"Successfully generated {count} biometric samples and trained LBPH model.", details
    else:
        return False, f"Generated samples, but training failed: {msg}", details

def verify_face_identity(account_number: str, image_data: str, threshold: float = 70.0) -> tuple[bool, str, dict]:
    """
    Verify face image against user's trained LBPH biometric model.
    Calibrated interpretation: Distance <= 70.0 indicates a match.
    Returns: (match: bool, message: str, details: dict)
    """
    models_dir = get_models_dir()
    model_path = models_dir / f"user_{account_number}.yml"

    if not model_path.exists():
        samples_dir = get_samples_dir(account_number)
        if len(list(samples_dir.glob("sample_*.jpg"))) >= 5:
            train_lbph_recognizer(account_number)
        if not model_path.exists():
            return False, f"No trained face biometric model found for account {account_number}. Please enroll first.", {}

    try:
        img_bgr = decode_image_base64(image_data)
        ok, msg, face_gray = validate_and_extract_face(img_bgr)
        if not ok:
            return False, msg, {}
    except ValueError as e:
        return False, str(e), {}

    # Load LBPH model
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(model_path))

    label, distance = recognizer.predict(face_gray)

    # Calculate calibrated confidence percentage (0 to 100%)
    # At distance 0 -> 100% confidence. At distance 70 -> ~50% confidence. Above 70 -> below threshold.
    if distance <= 0:
        confidence_pct = 100.0
    else:
        confidence_pct = max(0.0, min(100.0, 100.0 - (distance / threshold) * 50.0))

    match = (distance <= threshold)

    # Basic texture variance evaluation
    texture_var = float(cv2.Laplacian(face_gray, cv2.CV_64F).var())

    # Update last verified timestamp in database
    if match:
        execute_db(
            "UPDATE face_metadata SET last_verified_at = CURRENT_TIMESTAMP WHERE account_number = ?",
            (account_number,)
        )
        log_audit_event(None, account_number, "FACE_VERIFY_SUCCESS", f"Matched with distance {distance:.2f}", None, "SUCCESS")
        return True, f"Biometric verification successful. (Confidence: {confidence_pct:.1f}%)", {
            "match": True,
            "distance": round(distance, 2),
            "confidence_pct": round(confidence_pct, 1),
            "threshold": threshold,
            "texture_variance": round(texture_var, 1)
        }
    else:
        log_audit_event(None, account_number, "FACE_VERIFY_FAIL", f"Mismatched distance {distance:.2f} > {threshold}", None, "FAILURE")
        return False, f"Biometric verification failed. Face distance ({distance:.1f}) exceeds acceptance threshold ({threshold:.1f}).", {
            "match": False,
            "distance": round(distance, 2),
            "confidence_pct": round(confidence_pct, 1),
            "threshold": threshold,
            "texture_variance": round(texture_var, 1)
        }

def delete_user_face_data(account_number: str) -> tuple[bool, str]:
    """Authorized deletion of user's face samples and trained model."""
    samples_dir = get_samples_dir(account_number)
    models_dir = get_models_dir()
    model_path = models_dir / f"user_{account_number}.yml"

    deleted_samples = 0
    if samples_dir.exists():
        for f in samples_dir.glob("*.jpg"):
            try:
                f.unlink()
                deleted_samples += 1
            except Exception:
                pass
        try:
            samples_dir.rmdir()
        except Exception:
            pass

    if model_path.exists():
        try:
            model_path.unlink()
        except Exception:
            pass

    execute_db(
        """UPDATE face_metadata
           SET sample_count = 0, status = 'REVOKED'
           WHERE account_number = ?""",
        (account_number,)
    )
    log_audit_event(None, account_number, "DELETE_FACE_DATA", f"Revoked face model & deleted {deleted_samples} samples", None, "INFO")
    return True, f"Successfully removed {deleted_samples} face samples and revoked biometric model."
