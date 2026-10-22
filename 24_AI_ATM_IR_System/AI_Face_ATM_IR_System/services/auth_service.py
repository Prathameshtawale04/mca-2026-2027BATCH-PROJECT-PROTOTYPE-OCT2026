"""Authentication, PIN Cryptography, Lockout Tracking, and Authorization Service."""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, flash, request, abort
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import query_db, execute_db

def hash_password(password: str) -> str:
    """Generate secure password hash using Werkzeug PBKDF2/scrypt."""
    return generate_password_hash(password)

def check_password(password_hash: str, password: str) -> bool:
    """Verify password against Werkzeug hash."""
    return check_password_hash(password_hash, password)

def hash_pin(pin: str, salt: str = None) -> tuple[str, str]:
    """
    Hash 4-digit PIN using salted PBKDF2 HMAC-SHA256 with 100,000 iterations.
    Returns: (pin_hash_hex, salt_hex)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    salt_bytes = bytes.fromhex(salt)
    pin_bytes = pin.encode("utf-8")
    derived = hashlib.pbkdf2_hmac("sha256", pin_bytes, salt_bytes, 100000)
    return derived.hex(), salt

def verify_pin(pin: str, stored_hash: str, salt_hex: str) -> bool:
    """Verify PIN using constant-time string comparison to prevent timing attacks."""
    computed_hash, _ = hash_pin(pin, salt_hex)
    return secrets.compare_digest(computed_hash, stored_hash)

def log_audit_event(user_id=None, account_number=None, event_type="AUTH", details="", ip_address=None, status="INFO"):
    """Record an audit trail event into the audit_logs table."""
    if ip_address is None:
        try:
            ip_address = request.remote_addr or "127.0.0.1"
        except RuntimeError:
            ip_address = "127.0.0.1"
    execute_db(
        """INSERT INTO audit_logs (user_id, account_number, event_type, details, ip_address, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, account_number, event_type, details, ip_address, status)
    )

def is_user_locked(user: dict) -> bool:
    """Check if the account is currently locked due to failed attempts."""
    if not user.get("is_locked"):
        return False
    locked_until = user.get("locked_until")
    if locked_until is None:
        return True
    if isinstance(locked_until, str):
        try:
            locked_until_dt = datetime.fromisoformat(locked_until)
        except ValueError:
            locked_until_dt = datetime.strptime(locked_until, "%Y-%m-%d %H:%M:%S")
    else:
        locked_until_dt = locked_until
    
    if datetime.now() < locked_until_dt:
        return True
    
    # Auto-unlock if lock period expired
    execute_db(
        "UPDATE users SET is_locked = 0, failed_login_attempts = 0, locked_until = NULL WHERE id = ?",
        (user["id"],)
    )
    return False

def authenticate_user(username_or_email: str, password: str, ip_address: str = "127.0.0.1") -> tuple[bool, str, dict | None]:
    """
    Authenticate a user with username/email and password.
    Returns: (success: bool, message: str, user_dict | None)
    """
    user = query_db(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (username_or_email.strip(), username_or_email.strip().lower()),
        one=True
    )
    if not user:
        log_audit_event(None, None, "LOGIN_FAILED", f"Invalid user: {username_or_email}", ip_address, "FAILURE")
        return False, "Invalid username or password.", None

    user_dict = dict(user)

    if is_user_locked(user_dict):
        log_audit_event(user_dict["id"], None, "LOGIN_BLOCKED", "Attempt on locked account", ip_address, "WARNING")
        return False, "Account is locked due to multiple failed login attempts. Please try again later.", None

    if not check_password(user_dict["password_hash"], password):
        # Increment failed attempts
        new_attempts = user_dict["failed_login_attempts"] + 1
        if new_attempts >= 5:
            lock_until = datetime.now() + timedelta(minutes=15)
            execute_db(
                "UPDATE users SET failed_login_attempts = ?, is_locked = 1, locked_until = ? WHERE id = ?",
                (new_attempts, lock_until.strftime("%Y-%m-%d %H:%M:%S"), user_dict["id"])
            )
            log_audit_event(user_dict["id"], None, "ACCOUNT_LOCKED", "5 failed login attempts", ip_address, "WARNING")
            return False, "Account has been locked for 15 minutes due to 5 failed login attempts.", None
        else:
            execute_db(
                "UPDATE users SET failed_login_attempts = ? WHERE id = ?",
                (new_attempts, user_dict["id"])
            )
            log_audit_event(user_dict["id"], None, "LOGIN_FAILED", f"Failed attempt {new_attempts}/5", ip_address, "FAILURE")
            return False, f"Invalid username or password. ({5 - new_attempts} attempts remaining)", None

    # Reset failed attempts upon successful authentication
    execute_db(
        "UPDATE users SET failed_login_attempts = 0, is_locked = 0, locked_until = NULL WHERE id = ?",
        (user_dict["id"],)
    )
    
    # Fetch primary bank account if exists
    account = query_db("SELECT * FROM accounts WHERE user_id = ?", (user_dict["id"],), one=True)
    if account:
        user_dict["account_number"] = account["account_number"]
        user_dict["balance"] = account["balance"]
    else:
        user_dict["account_number"] = None
        user_dict["balance"] = 0.0

    log_audit_event(user_dict["id"], user_dict.get("account_number"), "LOGIN_SUCCESS", "User authenticated", ip_address, "SUCCESS")
    return True, "Login successful.", user_dict

def register_user(username: str, email: str, password: str, full_name: str, pin: str = "1234", role: str = "customer", initial_balance: float = 1000.0) -> tuple[bool, str, dict | None]:
    """Register a new user and generate a linked ATM bank account."""
    existing = query_db("SELECT id FROM users WHERE username = ? OR email = ?", (username.strip(), email.strip().lower()), one=True)
    if existing:
        return False, "Username or email is already registered.", None

    pwd_hash = hash_password(password)
    pin_hash_val, pin_salt_val = hash_pin(pin)

    res = execute_db(
        """INSERT INTO users (username, email, password_hash, role, full_name, pin_hash, pin_salt)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (username.strip(), email.strip().lower(), pwd_hash, role, full_name.strip(), pin_hash_val, pin_salt_val)
    )
    user_id = res["lastrowid"]

    # Generate random unique account number
    account_number = f"ACC{secrets.randbelow(9000) + 1000}"
    while query_db("SELECT id FROM accounts WHERE account_number = ?", (account_number,), one=True):
        account_number = f"ACC{secrets.randbelow(9000) + 1000}"

    execute_db(
        """INSERT INTO accounts (user_id, account_number, account_type, balance, daily_limit)
           VALUES (?, ?, 'SAVINGS', ?, 5000.0)""",
        (user_id, account_number, initial_balance)
    )

    log_audit_event(user_id, account_number, "REGISTER_USER", f"New user {username} created", None, "SUCCESS")
    user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    return True, "User registered successfully.", dict(user)

def login_required(f):
    """View decorator requiring an active authenticated session."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """View decorator restricting access to administrator role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in with administrator credentials.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if session.get("role") != "admin":
            flash("Access denied: Administrator privileges required.", "danger")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
