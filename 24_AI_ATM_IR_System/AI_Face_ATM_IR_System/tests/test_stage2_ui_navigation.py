"""Stage 2: Dashboard, Persistent Sidebar, and Common Navigation Test Suite."""

import pytest
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import init_db, close_db
from database.seed_demo_data import seed_all

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
    """Test HTTP client."""
    return app.test_client()

@pytest.fixture
def customer_client(app):
    """Authenticated customer client (Alex Vance)."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alex"
        sess["role"] = "customer"
        sess["full_name"] = "Dr. Alex Vance"
        sess["account_number"] = "ACC1001"
        sess["balance"] = 4850.0
    return c

@pytest.fixture
def admin_client(app):
    """Authenticated administrator client (Security Admin)."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "admin"
        sess["full_name"] = "System Security Admin"
        sess["account_number"] = "ADMIN01"
        sess["balance"] = 25000.0
    return c

def test_unauthenticated_redirects(client):
    """All protected destinations must redirect to /login when not authenticated."""
    protected_urls = [
        "/dashboard",
        "/face/register",
        "/face/verify",
        "/atm",
        "/finance",
        "/ir/language-models",
        "/ir/web-retrieval",
        "/ir/applications",
        "/search/hybrid",
        "/search/history",
        "/admin"
    ]
    for url in protected_urls:
        res = client.get(url)
        assert res.status_code == 302, f"URL {url} did not redirect"
        assert "/login" in res.headers["Location"], f"URL {url} did not redirect to /login"

def test_customer_sidebar_navigation(customer_client):
    """All 11 customer sidebar destinations must return HTTP 200."""
    customer_urls = [
        ("/dashboard", b"Hello, Dr. Alex Vance"),
        ("/face/register", b"Biometric Face Enrollment"),
        ("/face/verify", b"Live Biometric Verification"),
        ("/atm", b"ATM Terminal Simulator"),
        ("/finance", b"Personal Financial Assistance"),
        ("/ir/language-models", b"Unit IV: Language Models"),
        ("/ir/web-retrieval", b"Unit V: Web Retrieval"),
        ("/ir/applications", b"Unit VI: IR Applications"),
        ("/search/hybrid", b"Unified Hybrid Search"),
        ("/search/history", b"Search History"),
    ]
    for url, expected_text in customer_urls:
        res = customer_client.get(url)
        assert res.status_code == 200, f"URL {url} returned status {res.status_code}"
        assert expected_text in res.data, f"Expected text not found in {url}"

def test_admin_role_authorization(customer_client, admin_client):
    """Admin route must forbid customer (403) and allow admin (200)."""
    # Customer gets 403 Forbidden
    cust_res = customer_client.get("/admin")
    assert cust_res.status_code == 403
    assert b"403" in cust_res.data or b"Forbidden" in cust_res.data

    # Admin gets 200 OK
    admin_res = admin_client.get("/admin")
    assert admin_res.status_code == 200
    assert b"Security Operations Center" in admin_res.data
    assert b"Registered Users" in admin_res.data

def test_logout_clears_session(customer_client):
    """Logging out must clear session and redirect to /login."""
    res = customer_client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert b"signed out successfully" in res.data
