"""Main Application Routes (Landing, Dashboard, Health Check)."""

from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from services.auth_service import login_required
from database.db import query_db

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    """Application landing page redirecting to dashboard or login."""
    if "user_id" in session:
        return redirect(url_for("main.dashboard"))
    return render_template("login.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Executive student dashboard displaying financial stats, recent transactions, and quick links."""
    user_id = session.get("user_id")
    account_number = session.get("account_number")

    # Fetch active account info
    account = query_db("SELECT * FROM accounts WHERE user_id = ?", (user_id,), one=True)
    
    # Fetch recent transactions
    transactions = query_db(
        "SELECT * FROM transactions WHERE account_number = ? ORDER BY timestamp DESC LIMIT 5",
        (account_number,)
    )

    # Fetch savings goals
    goals = query_db("SELECT * FROM savings_goals WHERE user_id = ? ORDER BY id DESC LIMIT 3", (user_id,))

    # Fetch current month budget
    from datetime import datetime
    cur_month = datetime.now().strftime("%Y-%m")
    budget = query_db("SELECT * FROM budgets WHERE user_id = ? AND month_year = ?", (user_id, cur_month), one=True)

    # Calculate actual expenses this month
    expense_sum = query_db(
        """SELECT COALESCE(SUM(amount), 0.0) as total_spent
           FROM finance_entries
           WHERE user_id = ? AND entry_type = 'EXPENSE' AND strftime('%Y-%m', entry_date) = ?""",
        (user_id, cur_month),
        one=True
    )

    # Total documents in IR index
    doc_count = query_db("SELECT COUNT(*) as cnt FROM documents", one=True)["cnt"]

    return render_template(
        "dashboard.html",
        account=account,
        transactions=transactions,
        goals=goals,
        budget=budget,
        total_spent=expense_sum["total_spent"] if expense_sum else 0.0,
        doc_count=doc_count
    )

@main_bp.route("/api/health")
def health():
    """System health check endpoint."""
    return jsonify({
        "status": "healthy",
        "system": "Intelligent Face Recognition ATM & IR System",
        "version": "2.0.0",
        "database": "connected"
    })
