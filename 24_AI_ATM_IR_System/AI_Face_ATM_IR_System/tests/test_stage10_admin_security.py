"""Stage 10: Administrator Panel, Role-Based Access Control & Security Operations Test Suite."""

import pytest
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import init_db, close_db, query_db
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
def customer_client(app):
    """Client authenticated as standard customer."""
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
    """Client authenticated as system administrator."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 1
        sess["username"] = "admin"
        sess["role"] = "admin"
        sess["full_name"] = "Chief Security Officer"
        sess["account_number"] = "ADMIN01"
        sess["balance"] = 99999.0
    return c

def test_unauthenticated_admin_access_redirects(app):
    """Unauthenticated request to /admin must redirect to login."""
    client = app.test_client()
    res = client.get("/admin")
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]

def test_customer_role_forbidden_from_admin(customer_client):
    """Customers attempting to access admin routes or APIs must receive 403 Forbidden."""
    res_page = customer_client.get("/admin")
    assert res_page.status_code == 403

    res_users = customer_client.get("/admin/users")
    assert res_users.status_code == 403

    res_lock = customer_client.post("/admin/api/toggle_user_lock/2")
    assert res_lock.status_code == 403

    res_bal = customer_client.post("/admin/api/update_balance/ACC1001", json={"balance": 1000})
    assert res_bal.status_code == 403

def test_admin_portal_access(admin_client):
    """Administrator must have full access to /admin, /admin/users, and /admin/logs."""
    res_admin = admin_client.get("/admin")
    assert res_admin.status_code == 200
    assert b"Security Operations Center" in res_admin.data
    assert b"Chief Security Officer" in res_admin.data

    res_users = admin_client.get("/admin/users")
    assert res_users.status_code == 200

    res_logs = admin_client.get("/admin/logs")
    assert res_logs.status_code == 200

def test_admin_toggle_user_lock(admin_client, app):
    """Admin toggles user lock state and unlocks user, resetting failed attempts."""
    # 1. Lock customer Alex (id=2)
    res_lock = admin_client.post("/admin/api/toggle_user_lock/2")
    assert res_lock.status_code == 200
    assert res_lock.get_json()["is_locked"] is True

    with app.app_context():
        u = query_db("SELECT is_locked FROM users WHERE id = 2", one=True)
        assert u["is_locked"] == 1

    # 2. Unlock customer Alex (id=2)
    res_unlock = admin_client.post("/admin/api/toggle_user_lock/2")
    assert res_unlock.status_code == 200
    assert res_unlock.get_json()["is_locked"] is False

    with app.app_context():
        u = query_db("SELECT is_locked, failed_login_attempts FROM users WHERE id = 2", one=True)
        assert u["is_locked"] == 0
        assert u["failed_login_attempts"] == 0

def test_admin_update_balance(admin_client, app):
    """Admin updates account balance and verifies persistence."""
    res = admin_client.post("/admin/api/update_balance/ACC1001", json={"balance": 8250.75})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["new_balance"] == 8250.75

    with app.app_context():
        acc = query_db("SELECT balance FROM accounts WHERE account_number = 'ACC1001'", one=True)
        assert acc["balance"] == 8250.75

    # Negative balance validation
    res_neg = admin_client.post("/admin/api/update_balance/ACC1001", json={"balance": -50.0})
    assert res_neg.status_code == 400
    assert res_neg.get_json()["success"] is False

def test_admin_audit_logs_stream(admin_client):
    """Admin retrieves live audit trail records via JSON API."""
    res = admin_client.get("/admin/api/audit_logs")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "logs" in data
    assert len(data["logs"]) > 0
