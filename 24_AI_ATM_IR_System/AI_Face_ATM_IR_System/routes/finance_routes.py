"""Personal Finance & 50/30/20 Wealth Planning Routes and REST APIs."""

from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
from services.auth_service import login_required
from database.db import query_db
from services.finance_service import (
    add_finance_entry,
    calculate_50_30_20_summary,
    create_savings_goal,
    deposit_into_goal,
    delete_savings_goal
)

finance_bp = Blueprint("finance", __name__, url_prefix="/finance")

@finance_bp.route("")
@finance_bp.route("/")
@login_required
def index():
    """Financial assistance overview, 50/30/20 budgeting, and savings vaults."""
    user_id = session.get("user_id")
    cur_month = datetime.now().strftime("%Y-%m")
    
    summary = calculate_50_30_20_summary(user_id, cur_month)
    budget = query_db("SELECT * FROM budgets WHERE user_id = ? AND month_year = ?", (user_id, cur_month), one=True)
    entries = query_db(
        "SELECT * FROM finance_entries WHERE user_id = ? ORDER BY entry_date DESC LIMIT 20",
        (user_id,)
    )
    goals = query_db("SELECT * FROM savings_goals WHERE user_id = ? ORDER BY id DESC", (user_id,))

    return render_template(
        "finance/index.html",
        summary=summary,
        budget=budget,
        entries=entries,
        goals=goals,
        cur_month=cur_month
    )

@finance_bp.route("/api/summary")
@login_required
def api_summary():
    """Fetch 50/30/20 budget summary, category totals, and guidance tips."""
    user_id = session.get("user_id")
    month = request.args.get("month") or datetime.now().strftime("%Y-%m")
    summary = calculate_50_30_20_summary(user_id, month)
    return jsonify({"success": True, "summary": summary})

@finance_bp.route("/api/entry", methods=["POST"])
@login_required
def api_add_entry():
    """Add a new income or expense entry."""
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form
    entry_type = data.get("entry_type", "EXPENSE").upper()
    category = data.get("category", "General")
    
    try:
        amount = float(data.get("amount", 0.0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric amount"}), 400

    entry_date = data.get("entry_date")
    description = data.get("description", "")

    ok, msg, entry = add_finance_entry(user_id, entry_type, category, amount, entry_date, description)
    status_code = 200 if ok else 400
    return jsonify({"success": ok, "message": msg, "entry": entry}), status_code

@finance_bp.route("/api/goal", methods=["POST"])
@login_required
def api_add_goal():
    """Create a new savings goal vault."""
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form
    name = data.get("goal_name", "").strip()
    
    try:
        target = float(data.get("target_amount", 0.0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric target amount"}), 400

    target_date = data.get("target_date")

    ok, msg, goal = create_savings_goal(user_id, name, target, target_date)
    status_code = 200 if ok else 400
    return jsonify({"success": ok, "message": msg, "goal": goal}), status_code

@finance_bp.route("/api/goal/<int:goal_id>/deposit", methods=["POST"])
@login_required
def api_goal_deposit(goal_id):
    """Contribute savings into a vault."""
    user_id = session.get("user_id")
    data = request.get_json(silent=True) or request.form
    try:
        amount = float(data.get("amount", 0.0))
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid numeric amount"}), 400

    ok, msg, goal = deposit_into_goal(user_id, goal_id, amount)
    status_code = 200 if ok else 400
    return jsonify({"success": ok, "message": msg, "goal": goal}), status_code

@finance_bp.route("/api/goal/<int:goal_id>", methods=["DELETE"])
@login_required
def api_goal_delete(goal_id):
    """Delete a savings goal vault."""
    user_id = session.get("user_id")
    ok, msg = delete_savings_goal(user_id, goal_id)
    status_code = 200 if ok else 404
    return jsonify({"success": ok, "message": msg}), status_code
