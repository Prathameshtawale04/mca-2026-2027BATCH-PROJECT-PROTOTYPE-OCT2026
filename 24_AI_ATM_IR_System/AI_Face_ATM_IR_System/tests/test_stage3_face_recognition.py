"""Stage 3: Face Recognition, OpenCV Haar Detection & LBPH Verification Test Suite."""

import pytest
import os
import cv2
import numpy as np
import base64
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import init_db, close_db, query_db
from database.seed_demo_data import seed_all
from services.face_service import (
    decode_image_base64,
    validate_and_extract_face,
    save_face_sample,
    train_lbph_recognizer,
    verify_face_identity,
    delete_user_face_data,
    get_samples_dir
)

@pytest.fixture
def app():
    """Create test application configured with isolated test database."""
    test_db_path = Path(__file__).resolve().parent.parent / "data" / "test_atm_system.db"
    close_db()
    if test_db_path.exists():
        try:
            os.remove(test_db_path)
        except Exception:
            pass
    
    test_app = create_app(TestConfig)
    with test_app.app_context():
        init_db()
        seed_all()
    yield test_app

    close_db()
    if test_db_path.exists():
        try:
            os.remove(test_db_path)
        except Exception:
            pass

@pytest.fixture
def client(app):
    """Test HTTP client with authenticated customer session."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alex"
        sess["role"] = "customer"
        sess["full_name"] = "Dr. Alex Vance"
        sess["account_number"] = "ACC1001"
        sess["balance"] = 4850.0
    return c

def load_real_sample_b64(account_number="ACC1001"):
    """Load pre-seeded face sample from disk as base64 data URI."""
    base = Path(__file__).resolve().parent.parent / "data" / "face_data" / "samples" / account_number
    sample_file = base / "sample_000.jpg"
    if not sample_file.exists():
        pytest.skip(f"Pre-seeded sample {sample_file} not found")
    with open(sample_file, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode("utf-8")

def test_decode_image_base64():
    """Verify base64 decoding correctly extracts numpy matrix and rejects invalid payloads."""
    # Test valid 100x100 synthetic image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", img)
    b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")
    decoded = decode_image_base64(b64)
    assert decoded.shape == (100, 100, 3)

    # Test invalid payloads
    with pytest.raises(ValueError):
        decode_image_base64("")
    with pytest.raises(ValueError):
        decode_image_base64("not_base64_content")

def test_no_face_detection():
    """Blank or solid color image must fail face validation gracefully."""
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    ok, msg, _ = validate_and_extract_face(blank)
    assert ok is False
    assert "No face detected" in msg or "blurry" in msg

def test_real_sample_face_validation():
    """Pre-seeded sample must pass Haar detection and return 160x160 face ROI."""
    b64 = load_real_sample_b64("ACC1001")
    img_bgr = decode_image_base64(b64)
    ok, msg, face_gray = validate_and_extract_face(img_bgr)
    assert ok is True
    assert face_gray is not None
    assert face_gray.shape == (160, 160)

def test_lbph_training_and_verification(app):
    """Test full cycle: sample saving -> LBPH training -> positive and negative match verification."""
    with app.app_context():
        test_acc = "TEST_FACE_ACC"
        # 1. Save 8 samples of the same face
        b64 = load_real_sample_b64("ACC1001")
        img_bgr = decode_image_base64(b64)
        _, _, face_gray = validate_and_extract_face(img_bgr)
        
        for _ in range(8):
            save_face_sample(test_acc, face_gray)

        # 2. Train model
        ok, msg, details = train_lbph_recognizer(test_acc)
        assert ok is True
        assert details["samples_count"] >= 8

        # 3. Positive verification (own face)
        match, v_msg, v_details = verify_face_identity(test_acc, b64, threshold=70.0)
        assert match is True
        assert v_details["distance"] < 70.0
        assert v_details["confidence_pct"] >= 50.0

        # 4. Negative verification (different user face: Elena ACC1002)
        b64_elena = load_real_sample_b64("ACC1002")
        elena_match, elena_msg, elena_details = verify_face_identity(test_acc, b64_elena, threshold=50.0)
        # Elena's face should have higher distance and fail threshold
        assert elena_details["distance"] > v_details["distance"]

        # Cleanup test face data
        delete_user_face_data(test_acc)

def test_face_api_simulate_verify(client):
    """API endpoint /face/api/simulate_verify must verify active user against pre-enrolled samples."""
    res = client.post("/face/api/simulate_verify")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["match"] is True
    assert "details" in data
    assert data["details"]["distance"] <= 70.0

def test_face_api_delete_and_revoke(client, app):
    """API endpoint /face/api/delete must update database status to REVOKED."""
    # Temporarily copy sample files and model to keep test idempotent
    src_dir = Path(__file__).resolve().parent.parent / "data" / "face_data" / "samples" / "ACC1001"
    temp_backup = Path(__file__).resolve().parent.parent / "data" / "face_data" / "samples" / "_temp_ACC1001"
    model_file = Path(__file__).resolve().parent.parent / "data" / "face_data" / "models" / "user_ACC1001.yml"
    temp_model = Path(__file__).resolve().parent.parent / "data" / "face_data" / "models" / "_temp_user_ACC1001.yml"
    import shutil
    if src_dir.exists():
        shutil.copytree(src_dir, temp_backup, dirs_exist_ok=True)
    if model_file.exists():
        shutil.copy2(model_file, temp_model)

    try:
        res = client.post("/face/api/delete")
        assert res.status_code == 200
        assert res.get_json()["success"] is True

        with app.app_context():
            meta = query_db("SELECT * FROM face_metadata WHERE account_number = 'ACC1001'", one=True)
            assert meta["status"] == "REVOKED"
            assert meta["sample_count"] == 0
    finally:
        # Restore samples and model for subsequent runs and UI demo
        if temp_backup.exists():
            shutil.copytree(temp_backup, src_dir, dirs_exist_ok=True)
            shutil.rmtree(temp_backup, ignore_errors=True)
        if temp_model.exists():
            shutil.copy2(temp_model, model_file)
            temp_model.unlink(missing_ok=True)


