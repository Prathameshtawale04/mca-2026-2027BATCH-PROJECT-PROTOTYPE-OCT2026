import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from face_atm.anti_spoofing import BiometricAntiSpoofing

def test_anti_spoofing_evaluation():
    # Create test image with texture
    img = np.random.randint(50, 200, (200, 200, 3), dtype=np.uint8)
    report = BiometricAntiSpoofing.evaluate_liveness(img)

    assert "is_live" in report
    assert "liveness_score" in report
    assert "checks" in report
    assert len(report["checks"]) == 3
    assert any(c["test"] == "Laplacian Texture Variance" for c in report["checks"])
    assert any(c["test"] == "YCrCb Skin Chrominance" for c in report["checks"])
    assert any(c["test"] == "Screen Specular Glare" for c in report["checks"])

def test_anti_spoofing_glare_detection():
    # Create synthetic blown-out specular glare image (all 255)
    glare_img = np.ones((100, 100, 3), dtype=np.uint8) * 255
    report = BiometricAntiSpoofing.evaluate_liveness(glare_img)

    glare_check = next(c for c in report["checks"] if c["test"] == "Screen Specular Glare")
    assert glare_check["passed"] is False
