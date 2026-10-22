"""ATM Service: Balance Inquiry, Deposits, Withdrawals, Daily Limits, and Audit Ledger."""

import secrets
from datetime import datetime
from database.db import query_db, execute_db, db_transaction
from services.auth_service import verify_pin, log_audit_event

def get_account_by_number(account_number: str) -> dict | None:
    """Fetch active account record by account number."""
    acc = query_db("SELECT * FROM accounts WHERE account_number = ?", (account_number,), one=True)
    return dict(acc) if acc else None

def verify_atm_pin(account_number: str, pin: str) -> tuple[bool, str]:
    """
    Verify 4-digit PIN against user's salted PBKDF2 hash.
    Enforces 3-strike failed PIN attempt lockout policy.
    """
    user = query_db(
        """SELECT u.* FROM users u
           JOIN accounts a ON u.id = a.user_id
           WHERE a.account_number = ?""",
        (account_number,),
        one=True
    )
    if not user:
        return False, "Account record not found."

    user_dict = dict(user)
    if user_dict.get("is_locked"):
        return False, "Account is temporarily locked. Please contact security or try again later."

    if not verify_pin(pin, user_dict["pin_hash"], user_dict["pin_salt"]):
        new_failed = user_dict.get("failed_login_attempts", 0) + 1
        if new_failed >= 3:
            execute_db(
                "UPDATE users SET failed_login_attempts = ?, is_locked = 1 WHERE id = ?",
                (new_failed, user_dict["id"])
            )
            log_audit_event(user_dict["id"], account_number, "PIN_LOCKOUT", "3 incorrect PIN attempts", None, "WARNING")
            return False, "Account has been locked due to 3 consecutive incorrect PIN entries."
        else:
            execute_db("UPDATE users SET failed_login_attempts = ? WHERE id = ?", (new_failed, user_dict["id"]))
            log_audit_event(user_dict["id"], account_number, "PIN_FAILED", f"Incorrect PIN attempt {new_failed}/3", None, "FAILURE")
            return False, f"Incorrect PIN. ({3 - new_failed} attempts remaining)"

    # Reset failed counter on successful PIN
    execute_db("UPDATE users SET failed_login_attempts = 0 WHERE id = ?", (user_dict["id"],))
    return True, "PIN verified."

def calculate_dispenser_denominations(amount: float) -> dict:
    """Calculate physical banknote tray breakdown ($100, $50, $20 bills)."""
    remaining = int(amount)
    bills_100 = remaining // 100
    remaining %= 100
    bills_50 = remaining // 50
    remaining %= 50
    bills_20 = remaining // 20
    remaining %= 20
    bills_10 = remaining // 10
    return {
        "$100": bills_100,
        "$50": bills_50,
        "$20": bills_20,
        "$10": bills_10
    }

def process_withdrawal(account_number: str, pin: str, amount: float, description: str = "ATM Cash Withdrawal") -> tuple[bool, str, dict]:
    """
    Execute atomic cash withdrawal simulation with sufficient balance & daily limit enforcement.
    Returns: (success: bool, message: str, receipt_dict: dict)
    """
    if amount <= 0:
        return False, "Withdrawal amount must be greater than zero.", {}
    if amount % 10 != 0:
        return False, "Withdrawal amount must be a multiple of $10 for cash dispenser.", {}

    # Verify PIN
    pin_ok, pin_msg = verify_atm_pin(account_number, pin)
    if not pin_ok:
        return False, pin_msg, {}

    account = get_account_by_number(account_number)
    if not account or not account.get("is_active"):
        return False, "Account is inactive or disabled.", {}

    cur_balance = account["balance"]
    daily_limit = account["daily_limit"]
    acc_id = account["id"]

    # Check sufficient funds
    if cur_balance < amount:
        log_audit_event(account["user_id"], account_number, "WITHDRAWAL_FAILED", f"Insufficient funds: req ${amount:.2f}, bal ${cur_balance:.2f}", None, "FAILURE")
        return False, f"Insufficient funds. Available balance: ${cur_balance:.2f}", {}

    # Check daily withdrawal limit
    today_withdrawn_res = query_db(
        """SELECT COALESCE(SUM(amount), 0.0) as total_today
           FROM transactions
           WHERE account_id = ? AND type = 'WITHDRAWAL' AND date(timestamp) = date('now')""",
        (acc_id,),
        one=True
    )
    today_spent = today_withdrawn_res["total_today"] if today_withdrawn_res else 0.0

    if (today_spent + amount) > daily_limit:
        rem_limit = max(0.0, daily_limit - today_spent)
        log_audit_event(account["user_id"], account_number, "LIMIT_EXCEEDED", f"Exceeded daily limit: req ${amount:.2f}, rem ${rem_limit:.2f}", None, "WARNING")
        return False, f"Daily limit exceeded. Remaining daily limit today: ${rem_limit:.2f}", {}

    # Execute atomic SQLite transaction
    new_balance = cur_balance - amount
    ref_no = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.randbelow(900)+100}"

    try:
        with db_transaction():
            execute_db("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, acc_id), commit=False)
            execute_db(
                """INSERT INTO transactions (account_id, account_number, type, amount, balance_after, reference_no, description)
                   VALUES (?, ?, 'WITHDRAWAL', ?, ?, ?, ?)""",
                (acc_id, account_number, amount, new_balance, ref_no, description),
                commit=False
            )
            log_audit_event(account["user_id"], account_number, "WITHDRAWAL_SUCCESS", f"Dispensed ${amount:.2f} (Ref: {ref_no})", None, "SUCCESS")
    except Exception as e:
        return False, f"Database transaction rollback: {str(e)}", {}

    receipt = {
        "reference_no": ref_no,
        "type": "WITHDRAWAL",
        "amount": amount,
        "balance_before": cur_balance,
        "balance_after": new_balance,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "denominations": calculate_dispenser_denominations(amount)
    }

    return True, f"Cash dispensed successfully: ${amount:.2f}", receipt

def process_deposit(account_number: str, amount: float, description: str = "ATM Cash Deposit") -> tuple[bool, str, dict]:
    """
    Execute atomic cash deposit simulation.
    Returns: (success: bool, message: str, receipt_dict: dict)
    """
    if amount <= 0:
        return False, "Deposit amount must be greater than zero.", {}

    account = get_account_by_number(account_number)
    if not account or not account.get("is_active"):
        return False, "Account is inactive or disabled.", {}

    cur_balance = account["balance"]
    acc_id = account["id"]
    new_balance = cur_balance + amount
    ref_no = f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{secrets.randbelow(900)+100}"

    try:
        with db_transaction():
            execute_db("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, acc_id), commit=False)
            execute_db(
                """INSERT INTO transactions (account_id, account_number, type, amount, balance_after, reference_no, description)
                   VALUES (?, ?, 'DEPOSIT', ?, ?, ?, ?)""",
                (acc_id, account_number, amount, new_balance, ref_no, description),
                commit=False
            )
            log_audit_event(account["user_id"], account_number, "DEPOSIT_SUCCESS", f"Deposited ${amount:.2f} (Ref: {ref_no})", None, "SUCCESS")
    except Exception as e:
        return False, f"Database transaction rollback: {str(e)}", {}

    receipt = {
        "reference_no": ref_no,
        "type": "DEPOSIT",
        "amount": amount,
        "balance_before": cur_balance,
        "balance_after": new_balance,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return True, f"Cash deposited successfully: ${amount:.2f}", receipt

def get_mini_statement(account_number: str, limit: int = 10) -> list[dict]:
    """Fetch recent transaction mini statement for an account."""
    rows = query_db(
        "SELECT * FROM transactions WHERE account_number = ? ORDER BY timestamp DESC LIMIT ?",
        (account_number, limit)
    )
    return [dict(r) for r in rows]
