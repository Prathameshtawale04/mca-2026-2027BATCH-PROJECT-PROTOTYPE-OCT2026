"""Biometric ATM Security and Audit Service."""

import hashlib
import secrets
from database.db import execute_sql, query_all

def generate_salt(length: int = 16) -> str:
    return secrets.token_hex(length)

def hash_pin(pin: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        pin.encode("utf-8"),
        salt.encode("utf-8"),
        100000
    ).hex()

def log_security_event(account_number: str, event_type: str, details: str, ip_address: str = "127.0.0.1", status: str = "INFO"):
    try:
        execute_sql(
            """
            INSERT INTO audit_logs (account_number, event_type, details, ip_address, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (account_number, event_type, details, ip_address, status)
        )
    except Exception:
        pass

def verify_user_pin(account_number: str, entered_pin: str, ip_address: str = "127.0.0.1"):
    from services.atm_service import verify_atm_pin
    ok, msg = verify_atm_pin(account_number, entered_pin)
    if ok:
        log_security_event(account_number, "PIN_VERIFY_SUCCESS", "PIN successfully authenticated", ip_address, "SUCCESS")
        return True, "PIN authenticated successfully."
    else:
        log_security_event(account_number, "PIN_VERIFY_FAILED", msg, ip_address, "WARNING")
        return False, msg

def get_recent_security_logs(account_number: str = None, limit: int = 50):
    if account_number:
        return query_all(
            "SELECT * FROM audit_logs WHERE account_number = ? ORDER BY timestamp DESC LIMIT ?",
            (account_number, limit)
        )
    return query_all(
        "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
