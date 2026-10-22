import pytest
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import init_db
from database.seed_data import run_seed
from face_atm.security_service import generate_salt, hash_pin, verify_user_pin, get_recent_security_logs
from face_atm.atm_service import get_account_details, deposit, withdraw

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    run_seed()

def test_pin_hashing():
    salt = generate_salt()
    hash1 = hash_pin("1234", salt)
    hash2 = hash_pin("1234", salt)
    hash3 = hash_pin("9999", salt)
    
    assert hash1 == hash2
    assert hash1 != hash3
    assert len(hash1) == 64  # SHA-256 hex length

def test_valid_pin_verification():
    success, msg = verify_user_pin("ACC1001", "1234")
    assert success is True
    assert "authenticated successfully" in msg

def test_invalid_pin_verification():
    success, msg = verify_user_pin("ACC1001", "0000")
    assert success is False
    assert "remaining" in msg or "locked" in msg

def test_deposit_and_withdrawal():
    acc = "ACC1002"
    details_before = get_account_details(acc)
    balance_before = details_before["balance"]

    # Deposit
    dep_ok, dep_msg, dep_receipt = deposit(acc, 500.0, "Test Deposit")
    assert dep_ok is True
    assert dep_receipt["balance_after"] == round(balance_before + 500.0, 2)

    # Withdraw
    with_ok, with_msg, with_receipt = withdraw(acc, 200.0, "Test Withdrawal")
    assert with_ok is True
    assert with_receipt["balance_after"] == round(balance_before + 500.0 - 200.0, 2)

def test_invalid_withdrawal_multiples():
    acc = "ACC1002"
    # ATM requires multiple of $10
    ok, msg, receipt = withdraw(acc, 25.0)
    assert ok is False
    assert "multiples of $10" in msg
