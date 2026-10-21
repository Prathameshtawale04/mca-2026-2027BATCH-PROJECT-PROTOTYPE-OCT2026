"""Biometric Face Recognition Routes (Registration, Verification, Training & Deletion)."""

import os
import base64
import cv2
import numpy as np
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, session
from services.auth_service import login_required
from database.db import query_db
from services.face_service import (
    decode_image_base64,
    validate_and_extract_face,
    save_face_sample,
    train_lbph_recognizer,
    verify_face_identity,
    delete_user_face_data,
    get_samples_dir,
    generate_synthetic_samples_for_account
)

face_bp = Blueprint("face", __name__, url_prefix="/face")

@face_bp.route("/register")
@login_required
def register_page():
    """Face biometric registration and sample collection page."""
    user_id = session.get("user_id")
    metadata = query_db("SELECT * FROM face_metadata WHERE user_id = ?", (user_id,), one=True)
    return render_template("face/register.html", metadata=metadata)

@face_bp.route("/verify")
@login_required
def verify_page():
    """Live webcam biometric verification and distance scoring page."""
    user_id = session.get("user_id")
    metadata = query_db("SELECT * FROM face_metadata WHERE user_id = ?", (user_id,), one=True)
    return render_template("face/verify.html", metadata=metadata)

@face_bp.route("/api/capture_sample", methods=["POST"])
@login_required
def capture_sample():
    """Capture and validate a single face sample submitted via webcam."""
    account_number = session.get("account_number")
    data = request.get_json(silent=True) or {}
    image_data = data.get("image")

    if not image_data:
        return jsonify({"success": False, "message": "Missing image payload"}), 400

    try:
        img_bgr = decode_image_base64(image_data)
        ok, msg, face_gray = validate_and_extract_face(img_bgr)
        if not ok:
            return jsonify({"success": False, "message": msg}), 400

        count = save_face_sample(account_number, face_gray)
        return jsonify({
            "success": True,
            "message": f"Sample #{count} saved successfully.",
            "sample_count": count
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Sample capture error: {str(e)}"}), 500

@face_bp.route("/api/train", methods=["POST"])
@login_required
def train_model():
    """Train LBPH Face Recognizer using stored samples for current user."""
    account_number = session.get("account_number")
    ok, msg, details = train_lbph_recognizer(account_number)
    status_code = 200 if ok else 400
    return jsonify({"success": ok, "message": msg, "details": details}), status_code

@face_bp.route("/api/verify", methods=["POST"])
@login_required
def verify_face():
    """Perform real-time LBPH biometric match against live webcam image."""
    account_number = session.get("account_number")
    data = request.get_json(silent=True) or {}
    image_data = data.get("image")

    if not image_data:
        return jsonify({"success": False, "message": "No image payload provided"}), 400

    match, msg, details = verify_face_identity(account_number, image_data)
    return jsonify({
        "success": match,
        "match": match,
        "message": msg,
        "details": details
    })

@face_bp.route("/api/simulate_verify", methods=["POST"])
@login_required
def simulate_verify():
    """
    Demonstration helper for testing/viva without physical webcam:
    Loads one of the registered user's enrolled sample files, encodes it,
    and runs it through the exact real LBPH verification pipeline.
    """
    account_number = session.get("account_number")
    samples_dir = get_samples_dir(account_number)
    sample_files = list(samples_dir.glob("sample_*.jpg"))

    if not sample_files:
        return jsonify({
            "success": False,
            "message": f"No enrolled face sample images found on disk for {account_number}. Please capture samples first."
        }), 404

    # Read first available sample image
    with open(sample_files[0], "rb") as f:
        img_b64 = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

    match, msg, details = verify_face_identity(account_number, img_b64)
    return jsonify({
        "success": match,
        "match": match,
        "message": msg + " (Evaluated from enrolled biometric sample)",
        "details": details
    })

@face_bp.route("/api/delete", methods=["POST"])
@login_required
def delete_face():
    """Revoke biometric registration and delete stored face images."""
    account_number = session.get("account_number")
    ok, msg = delete_user_face_data(account_number)
    return jsonify({"success": ok, "message": msg})

@face_bp.route("/api/generate_synthetic", methods=["POST"])
@login_required
def generate_synthetic():
    """Generate synthetic biometric samples and train LBPH model for current user."""
    account_number = session.get("account_number")
    ok, msg, details = generate_synthetic_samples_for_account(account_number, count=15)
    status_code = 200 if ok else 400
    return jsonify({"success": ok, "message": msg, "details": details}), status_code

@face_bp.route("/api/upload_sample", methods=["POST"])
@login_required
def upload_sample():
    """Upload a face photo file, detect face, and extract training samples."""
    account_number = session.get("account_number")
    data = request.get_json(silent=True) or {}
    image_data = data.get("image")

    if not image_data:
        return jsonify({"success": False, "message": "No photo image data received"}), 400

    try:
        img_bgr = decode_image_base64(image_data)
        ok, msg, face_gray = validate_and_extract_face(img_bgr)
        if not ok:
            return jsonify({"success": False, "message": msg}), 400

        # Save base sample
        count = save_face_sample(account_number, face_gray)
        # Augment with slight brightness/contrast variations so LBPH gets at least 5 samples
        for delta in [-12, -6, 6, 12]:
            varied = np.clip(face_gray.astype(np.int16) + delta, 0, 255).astype(np.uint8)
            count = save_face_sample(account_number, varied)

        return jsonify({
            "success": True,
            "message": f"Face successfully detected and enrolled! Total samples on file: {count}.",
            "sample_count": count
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Upload processing error: {str(e)}"}), 500
