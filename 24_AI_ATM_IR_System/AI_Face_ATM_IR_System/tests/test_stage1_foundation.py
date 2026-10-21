"""Stage 1: Foundation & Authentication Test Suite."""

import pytest
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import query_db, init_db, close_db
from database.seed_demo_data import seed_all
from services.auth_service import (
    hash_password,
    check_password,
    hash_pin,
    verify_pin,
    authenticate_user,
    register_user
)

@pytest.fixture
def app():
    """Create test application configured with isolated test database."""
    test_db_path = Path(__file__).resolve().parent.parent / "data" / "test_atm_system.db"
    # Close any lingering connections and remove old test db
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
    """Test HTTP client."""
    return app.test_client()

def test_database_tables_exist(app):
    """Verify that all 16 required tables exist in SQLite."""
    with app.app_context():
        tables = query_db("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [t["name"] for t in tables]
        expected = [
            "users", "accounts", "transactions", "face_metadata",
            "finance_entries", "budgets", "savings_goals", "documents",
            "passages", "inverted_index", "crawl_pages", "links",
            "search_history", "user_interactions", "knowledge_triples", "audit_logs"
        ]
        for exp in expected:
            assert exp in table_names, f"Expected table '{exp}' not found in SQLite database"

def test_password_hashing():
    """Verify password hashing produces distinct hashes and validates correctly."""
    pwd = "SecureBankingPassword2026!"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert check_password(hashed, pwd) is True
    assert check_password(hashed, "WrongPassword") is False

def test_pbkdf2_pin_hashing():
    """Verify salted PBKDF2 HMAC-SHA256 PIN hashing and constant-time verification."""
    pin = "1234"
    h1, salt1 = hash_pin(pin)
    h2, salt2 = hash_pin(pin)
    # Different random salts must yield different hashes
    assert salt1 != salt2
    assert h1 != h2
    # But verification against own salt succeeds
    assert verify_pin("1234", h1, salt1) is True
    assert verify_pin("5678", h1, salt1) is False

def test_demo_users_authentication(app):
    """Verify pre-seeded demo accounts can authenticate successfully."""
    with app.app_context():
        # Test Alex
        ok, msg, user = authenticate_user("alex", "password123")
        assert ok is True
        assert user["username"] == "alex"
        assert user["role"] == "customer"
        assert user["account_number"] == "ACC1001"

        # Test Admin
        ok, msg, admin = authenticate_user("admin", "admin123")
        assert ok is True
        assert admin["role"] == "admin"
        assert admin["account_number"] == "ADMIN01"

        # Test Invalid Password
        ok, msg, _ = authenticate_user("alex", "WrongPassword")
        assert ok is False
        assert "Invalid username or password" in msg

def test_user_registration(app):
    """Verify registering a new demo customer creates linked user and account."""
    with app.app_context():
        ok, msg, user = register_user("marcus", "marcus@test.local", "pass123", "Marcus Brody", pin="4321")
        assert ok is True
        assert user["username"] == "marcus"

        acc = query_db("SELECT * FROM accounts WHERE user_id = ?", (user["id"],), one=True)
        assert acc is not None
        assert acc["account_number"].startswith("ACC")
        assert acc["balance"] == 1000.0

def test_account_lockout_after_failed_attempts(app):
    """Verify 5 consecutive failed login attempts trigger temporary account lockout."""
    with app.app_context():
        # Create dedicated test user
        register_user("locktest", "locktest@test.local", "correctpass", "Lockout Tester")
        
        # 4 failed attempts
        for _ in range(4):
            ok, msg, _ = authenticate_user("locktest", "wrong")
            assert ok is False

        # 5th failed attempt should lock account
        ok, msg, _ = authenticate_user("locktest", "wrong")
        assert ok is False
        assert "locked" in msg.lower()

        # Subsequent attempt with correct password must be blocked
        ok, msg, _ = authenticate_user("locktest", "correctpass")
        assert ok is False
        assert "locked" in msg.lower()

def test_http_routes(client):
    """Verify landing page, health check, login, and dashboard redirect."""
    # Health check
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"

    # Landing page
    res = client.get("/")
    assert res.status_code == 200
    assert b"Sign In" in res.data or b"Smart ATM" in res.data

    # Protected dashboard redirects to login when unauthenticated
    res = client.get("/dashboard")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]

def test_api_demo_login(client):
    """Verify 1-click viva demo login sets session and redirects to dashboard."""
    res = client.post("/api/auth/demo_login", json={"username": "alex"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "dashboard" in data["redirect_url"]

    # Session is now authenticated, dashboard loads with 200
    res2 = client.get("/dashboard")
    assert res2.status_code == 200
    assert b"Dr. Alex Vance" in res2.data
    assert b"ACC1001" in res2.data
