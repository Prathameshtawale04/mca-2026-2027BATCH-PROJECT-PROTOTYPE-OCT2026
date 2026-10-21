"""ATM Simulator Routes (Terminal UI & REST APIs for Withdraw, Deposit, Balance, Statement)."""

from flask import Blueprint, render_template, request, jsonify, session
from services.auth_service import login_required
from database.db import query_db
from services.atm_service import (
    get_account_by_number,
    process_withdrawal,
    process_deposit,
    get_mini_statement
)

atm_bp = Blueprint("atm", __name__, url_prefix="/atm")

@atm_bp.route("")
@atm_bp.route("/")
@login_required
def index():
    """ATM simulator terminal interface with tactile keypad and transaction ledger."""
    user_id = session.get("user_id")
    account = query_db("SELECT * FROM accounts WHERE user_id = ?", (user_id,), one=True)
    transactions = query_db(
        "SELECT * FROM transactions WHERE account_id = ? ORDER BY timestamp DESC LIMIT 10",
        (account["id"] if account else 0,)
    )
    return render_template("atm/index.html", account=account, transactions=transactions)

@atm_bp.route("/api/balance")
@login_required
def api_balance():
    """Balance enquiry API endpoint."""
    account_number = session.get("account_number")
    acc = get_account_by_number(account_number)
    if not acc:
        return jsonify({"success": False, "message": "Account not found"}), 404
    session["balance"] = acc["balance"]
    return jsonify({
        "success": True,
        "account_number": account_number,
        "balance": acc["balance"],
        "daily_limit": acc["daily_limit"],
        "account_type": acc["account_type"]
    })

@atm_bp.route("/api/withdraw", methods=["POST"])
@login_required
def api_withdraw():
    """ATM cash withdrawal API endpoint with PIN and limit verification."""
    account_number = session.get("account_number")
    data = request.get_json(silent=True) or request.form
    pin = data.get("pin", "").strip()
    
    try:
        amount = float(data.get("amount", 0.0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric amount"}), 400

    desc = data.get("description", "ATM Cash Withdrawal")

    ok, msg, receipt = process_withdrawal(account_number, pin, amount, desc)
    if ok:
        session["balance"] = receipt["balance_after"]
        return jsonify({"success": True, "message": msg, "receipt": receipt})
    else:
        return jsonify({"success": False, "message": msg}), 400

@atm_bp.route("/api/deposit", methods=["POST"])
@login_required
def api_deposit():
    """ATM cash deposit API endpoint."""
    account_number = session.get("account_number")
    data = request.get_json(silent=True) or request.form
    
    try:
        amount = float(data.get("amount", 0.0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric amount"}), 400

    desc = data.get("description", "ATM Cash Deposit")

    ok, msg, receipt = process_deposit(account_number, amount, desc)
    if ok:
        session["balance"] = receipt["balance_after"]
        return jsonify({"success": True, "message": msg, "receipt": receipt})
    else:
        return jsonify({"success": False, "message": msg}), 400

@atm_bp.route("/api/statement")
@login_required
def api_statement():
    """ATM mini statement API endpoint."""
    account_number = session.get("account_number")
    statement = get_mini_statement(account_number, limit=10)
    return jsonify({"success": True, "statement": statement})
