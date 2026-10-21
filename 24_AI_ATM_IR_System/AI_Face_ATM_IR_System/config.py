"""Application Configuration Settings."""

import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "mira-ai-secure-atm-ir-secret-key-2026")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")

    # Primary SQLite Database Location
    DATABASE_PATH = BASE_DIR / "data" / "atm_system.db"

    # Session Security
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max payload

    # Biometric Face Recognition Settings
    FACE_DATA_DIR = BASE_DIR / "data" / "face_data"
    FACE_SAMPLES_DIR = FACE_DATA_DIR / "samples"
    FACE_MODELS_DIR = FACE_DATA_DIR / "models"
    HAAR_CASCADE_PATH = str(BASE_DIR / "data" / "haarcascade_frontalface_default.xml")
    
    # LBPH Recognition Parameters (distance <= threshold indicates match)
    LBPH_CONFIDENCE_THRESHOLD = 70.0
    SAMPLE_CAPTURE_COUNT = 30

    # ATM & Authentication Security Policy
    MAX_FAILED_LOGIN_ATTEMPTS = 5
    MAX_FAILED_PIN_ATTEMPTS = 3
    ACCOUNT_LOCK_MINUTES = 15

    # Crawling Settings (controlled local data safety)
    CRAWLER_MAX_DEPTH = 2
    CRAWLER_MAX_PAGES = 15
    CRAWLER_DELAY_SECONDS = 0.5
    CRAWLER_USER_AGENT = "AcademicIRBot/1.0 (+http://localhost:5000/)"

    # Document & Dataset Storage Paths
    DOCUMENTS_DIR = BASE_DIR / "data" / "documents"
    CRAWL_DATA_DIR = BASE_DIR / "data" / "crawl_data"
    DATASETS_DIR = BASE_DIR / "data" / "datasets"

class TestConfig(Config):
    TESTING = True
    DATABASE_PATH = BASE_DIR / "data" / "test_atm_system.db"
    WTF_CSRF_ENABLED = False
