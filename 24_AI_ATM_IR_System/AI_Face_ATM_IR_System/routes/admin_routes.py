"""Administrator Security Operations Center (SOC) Routes."""

from flask import Blueprint, render_template, request, jsonify, session
from services.auth_service import admin_required
from database.db import query_db, execute_sql

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("")
@admin_bp.route("/")
@admin_required
def index():
    """Administrator security center, user management, audit logs, and operational telemetry."""
    users = query_db(
        """SELECT u.*, a.account_number, a.balance, a.is_active as acc_active, fm.sample_count, fm.status as face_status
           FROM users u
           LEFT JOIN accounts a ON u.id = a.user_id
           LEFT JOIN face_metadata fm ON u.id = fm.user_id
           ORDER BY u.id ASC"""
    )
    audit_logs = query_db("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
    
    # Aggregates
    user_cnt = len(users)
    total_deposits = query_db("SELECT COALESCE(SUM(balance), 0.0) as total FROM accounts", one=True)["total"]
    audit_cnt = query_db("SELECT COUNT(*) as cnt FROM audit_logs", one=True)["cnt"]
    doc_cnt = query_db("SELECT COUNT(*) as cnt FROM documents", one=True)["cnt"]

    return render_template(
        "admin/index.html",
        users=users,
        audit_logs=audit_logs,
        user_cnt=user_cnt,
        total_deposits=total_deposits,
        audit_cnt=audit_cnt,
        doc_cnt=doc_cnt
    )

@admin_bp.route("/users")
@admin_required
def users_view():
    """Alias for user management view."""
    return index()

@admin_bp.route("/logs")
@admin_required
def logs_view():
    """Alias for audit logs view."""
    return index()

@admin_bp.route("/api/toggle_user_lock/<int:user_id>", methods=["POST"])
@admin_required
def toggle_user_lock(user_id):
    """Toggle a user's is_locked state between 0 and 1, resetting strikes if unlocked."""
    user = query_db("SELECT id, username, is_locked, failed_login_attempts FROM users WHERE id = ?", (user_id,), one=True)
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    new_state = 0 if user["is_locked"] else 1
    new_attempts = 0 if new_state == 0 else user["failed_login_attempts"]

    execute_sql(
        "UPDATE users SET is_locked = ?, failed_login_attempts = ? WHERE id = ?",
        (new_state, new_attempts, user_id)
    )

    action_label = "UNLOCKED" if new_state == 0 else "LOCKED"
    admin_acc = session.get("account_number", "ADMIN")
    
    try:
        execute_sql(
            """INSERT INTO audit_logs (user_id, account_number, event_type, status, details)
               VALUES (?, ?, 'ADMIN_OVERRIDE', 'SUCCESS', ?)""",
            (user_id, admin_acc, f"Admin {action_label} account for user @{user['username']}")
        )
    except Exception:
        pass

    return jsonify({
        "success": True,
        "is_locked": bool(new_state),
        "message": f"User @{user['username']} successfully {action_label.lower()}."
    })

@admin_bp.route("/api/update_balance/<account_number>", methods=["POST"])
@admin_required
def update_balance(account_number):
    """Admin override to adjust account balance for testing/demo scenarios."""
    data = request.get_json(silent=True) or request.form
    new_balance = float(data.get("balance", 0.0))
    if new_balance < 0:
        return jsonify({"success": False, "message": "Balance cannot be negative"}), 400

    execute_sql("UPDATE accounts SET balance = ? WHERE account_number = ?", (new_balance, account_number))

    try:
        execute_sql(
            """INSERT INTO audit_logs (account_number, event_type, status, details)
               VALUES (?, 'ADMIN_OVERRIDE', 'SUCCESS', ?)""",
            (account_number, f"Admin updated balance to ${new_balance:.2f}")
        )
    except Exception:
        pass

    return jsonify({
        "success": True,
        "account_number": account_number,
        "new_balance": new_balance,
        "message": f"Account {account_number} balance updated to ${new_balance:.2f}"
    })

@admin_bp.route("/api/audit_logs", methods=["GET"])
@admin_required
def api_audit_logs():
    """Retrieve raw audit trail events as JSON."""
    logs = query_db("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 100")
    return jsonify({"success": True, "logs": [dict(l) for l in logs]})
