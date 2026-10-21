"""Stage 4: ATM Simulation, PIN Verification, Daily Limits & ACID Transactions Test Suite."""

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
from services.atm_service import (
    get_account_by_number,
    verify_atm_pin,
    calculate_dispenser_denominations,
    process_withdrawal,
    process_deposit,
    get_mini_statement
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

    close_db()
    if test_db_path.exists():
        try:
            os.remove(test_db_path)
        except Exception:
            pass

@pytest.fixture
def client(app):
    """Test HTTP client with authenticated customer session (Alex ACC1001)."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alex"
        sess["role"] = "customer"
        sess["full_name"] = "Dr. Alex Vance"
        sess["account_number"] = "ACC1001"
        sess["balance"] = 4850.0
    return c

def test_dispenser_denominations():
    """Verify banknote breakdown calculation for cash dispenser tray."""
    denom = calculate_dispenser_denominations(280)
    assert denom["$100"] == 2
    assert denom["$50"] == 1
    assert denom["$20"] == 1
    assert denom["$10"] == 1

def test_atm_pin_verification_and_lockout(app):
    """Verify PIN authentication and 3-strike account lockout."""
    with app.app_context():
        # Correct PIN
        ok, msg = verify_atm_pin("ACC1001", "1234")
        assert ok is True

        # Incorrect PIN 1
        ok, msg = verify_atm_pin("ACC1001", "0000")
        assert ok is False
        assert "2 attempts remaining" in msg

        # Incorrect PIN 2
        ok, msg = verify_atm_pin("ACC1001", "0000")
        assert ok is False
        assert "1 attempts remaining" in msg

        # Incorrect PIN 3 -> Account Locked
        ok, msg = verify_atm_pin("ACC1001", "0000")
        assert ok is False
        assert "locked" in msg.lower()

        # Subsequent attempt with correct PIN is blocked
        ok, msg = verify_atm_pin("ACC1001", "1234")
        assert ok is False
        assert "locked" in msg.lower()

        # Restore unlocked state for subsequent independent test isolation
        from database.db import execute_db
        execute_db("UPDATE users SET is_locked = 0, failed_login_attempts = 0, locked_until = NULL WHERE username = 'alex'")

def test_atomic_withdrawal_and_balance_checks(app):
    """Verify cash withdrawal decreases balance atomically and generates reference number."""
    with app.app_context():
        acc = get_account_by_number("ACC1002")
        initial_bal = acc["balance"]

        # Withdraw $100 with correct PIN 5678
        ok, msg, receipt = process_withdrawal("ACC1002", "5678", 100.0, "Test Withdrawal")
        assert ok is True
        assert receipt["balance_after"] == initial_bal - 100.0
        assert receipt["reference_no"].startswith("TXN-")
        assert receipt["denominations"]["$100"] == 1

        # Check transaction in database
        tx = query_db("SELECT * FROM transactions WHERE reference_no = ?", (receipt["reference_no"],), one=True)
        assert tx is not None
        assert tx["amount"] == 100.0
        assert tx["type"] == "WITHDRAWAL"

def test_withdrawal_insufficient_funds(app):
    """Withdrawal exceeding account balance must fail."""
    with app.app_context():
        acc = get_account_by_number("ACC1001")
        excess_amount = acc["balance"] + 5000.0
        ok, msg, _ = process_withdrawal("ACC1001", "1234", excess_amount)
        assert ok is False
        assert "Insufficient funds" in msg

def test_withdrawal_daily_limit_exceeded(app):
    """Withdrawal exceeding account daily limit must fail."""
    with app.app_context():
        acc = get_account_by_number("ACC1001")
        limit = acc["daily_limit"]
        ok, msg, _ = process_withdrawal("ACC1001", "1234", limit + 100.0)
        assert ok is False
        assert "Daily limit exceeded" in msg

def test_atomic_deposit(app):
    """Cash deposit must increase balance atomically and record transaction."""
    with app.app_context():
        acc = get_account_by_number("ACC1001")
        orig_bal = acc["balance"]

        ok, msg, receipt = process_deposit("ACC1001", 250.0, "Test Cash Deposit")
        assert ok is True
        assert receipt["balance_after"] == orig_bal + 250.0

        updated_acc = get_account_by_number("ACC1001")
        assert updated_acc["balance"] == orig_bal + 250.0

def test_atm_api_endpoints(client):
    """Test /atm/api/balance, /atm/api/deposit, and /atm/api/withdraw via HTTP client."""
    # 1. Balance Enquiry
    res_bal = client.get("/atm/api/balance")
    assert res_bal.status_code == 200
    data_bal = res_bal.get_json()
    assert data_bal["success"] is True
    cur_bal = data_bal["balance"]

    # 2. Deposit $200
    res_dep = client.post("/atm/api/deposit", json={"amount": 200.0, "description": "Client Deposit"})
    assert res_dep.status_code == 200
    data_dep = res_dep.get_json()
    assert data_dep["success"] is True
    assert data_dep["receipt"]["balance_after"] == cur_bal + 200.0

    # 3. Withdraw $50
    res_wdl = client.post("/atm/api/withdraw", json={"amount": 50.0, "pin": "1234"})
    assert res_wdl.status_code == 200
    data_wdl = res_wdl.get_json()
    assert data_wdl["success"] is True
    assert data_wdl["receipt"]["balance_after"] == cur_bal + 150.0

    # 4. Mini Statement
    res_stmt = client.get("/atm/api/statement")
    assert res_stmt.status_code == 200
    statement = res_stmt.get_json()["statement"]
    assert len(statement) >= 2
    assert statement[0]["reference_no"].startswith("TXN-")
