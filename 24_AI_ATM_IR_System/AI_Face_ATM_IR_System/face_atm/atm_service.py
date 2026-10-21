"""ATM Financial Transaction Service (Adapter for Face ATM Module)."""

import uuid
from datetime import datetime
from database.db import query_one, query_all, execute_sql
from services.atm_service import get_account_by_number, process_deposit

def get_account_details(account_number: str):
    return query_one(
        """
        SELECT a.account_number, a.balance, a.daily_limit, a.created_at,
               u.full_name, u.email, u.is_locked
        FROM accounts a
        JOIN users u ON a.user_id = u.id
        WHERE a.account_number = ?
        """,
        (account_number,)
    )

def deposit(account_number: str, amount: float, description: str = "ATM Cash Deposit"):
    ok, msg, receipt = process_deposit(account_number, amount, description)
    return ok, msg, receipt

def withdraw(account_number: str, amount: float, description: str = "ATM Cash Withdrawal"):
    if amount <= 0:
        return False, "Withdrawal amount must be greater than $0.00.", None
    if amount % 10 != 0:
        return False, "ATM cash dispenser only issues multiples of $10 ($10, $20, $50, $100).", None

    acc = get_account_by_number(account_number)
    if not acc:
        return False, "Account record not found.", None
    if acc["balance"] < amount:
        return False, f"Insufficient funds. Current balance: ${acc['balance']:.2f}", None

    new_bal = round(acc["balance"] - amount, 2)
    execute_sql("UPDATE accounts SET balance = ? WHERE id = ?", (new_bal, acc["id"]))
    ref = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    execute_sql(
        """INSERT INTO transactions (account_id, account_number, type, amount, balance_after, description, reference_no)
           VALUES (?, ?, 'WITHDRAWAL', ?, ?, ?, ?)""",
        (acc["id"], account_number, amount, new_bal, description, ref)
    )

    return True, f"Successfully withdrew ${amount:.2f}.", {
        "account_number": account_number,
        "type": "WITHDRAWAL",
        "amount": amount,
        "balance_after": new_bal,
        "reference_id": ref,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def get_transaction_history(account_number: str, limit: int = 20):
    return query_all(
        """SELECT t.* FROM transactions t
           JOIN accounts a ON t.account_id = a.id
           WHERE a.account_number = ?
           ORDER BY t.timestamp DESC LIMIT ?""",
        (account_number, limit)
    )
