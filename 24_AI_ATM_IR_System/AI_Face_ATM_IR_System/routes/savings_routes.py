from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.database import db, User, Account, Transaction, SavingsGoal, AuditLog
from services.recommendation_service import generate_savings_recommendations

savings_bp = Blueprint("savings", __name__, url_prefix="/api/savings")

@savings_bp.route("/goals", methods=["GET"])
@jwt_required()
def get_goals():
    user_id = int(get_jwt_identity())
    goals = SavingsGoal.query.filter_by(user_id=user_id).order_by(SavingsGoal.created_at.desc()).all()
    return jsonify({"goals": [g.to_dict() for g in goals]})


@savings_bp.route("/goals", methods=["POST"])
@jwt_required()
def create_goal():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    category = data.get("category", "General")
    target_amount = float(data.get("target_amount", 500))
    initial_amount = float(data.get("initial_amount", 0))

    if not title or target_amount <= 0:
        return jsonify({"error": "Title and positive target amount are required"}), 400

    goal = SavingsGoal(
        user_id=user_id,
        title=title,
        category=category,
        target_amount=target_amount,
        current_amount=initial_amount,
        auto_save_pct=float(data.get("auto_save_pct", 5.0))
    )
    db.session.add(goal)
    db.session.commit()

    return jsonify({"message": "Savings goal created", "goal": goal.to_dict()}), 201


@savings_bp.route("/goals/<int:goal_id>/contribute", methods=["POST"])
@jwt_required()
def contribute_to_goal(goal_id):
    user_id = int(get_jwt_identity())
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=user_id).first_or_404()
    account = Account.query.filter_by(user_id=user_id).first_or_404()

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid contribution amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Contribution amount must be positive"}), 400

    if amount > account.balance:
        return jsonify({"error": f"Insufficient funds. Account balance: ${account.balance:,.2f}"}), 400

    # Transfer from checking account to savings goal
    account.balance -= amount
    goal.current_amount += amount

    if goal.current_amount >= goal.target_amount:
        goal.status = "reached"

    # Create transaction
    tx = Transaction(
        account_id=account.id,
        type="transfer",
        amount=amount,
        status="completed",
        fraud_score=0.01,
        is_flagged=False,
        description=f"Savings Contribution to '{goal.title}'",
        channel="atm"
    )
    db.session.add(tx)

    audit = AuditLog(
        user_id=user_id,
        action="GOAL_CONTRIBUTION",
        resource="savings_goal",
        details=f"Contributed ${amount:.2f} to goal {goal.title}"
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        "message": f"Successfully contributed ${amount:,.2f} to '{goal.title}'!",
        "goal": goal.to_dict(),
        "new_balance": round(account.balance, 2)
    })


@savings_bp.route("/recommendations", methods=["GET"])
@jwt_required()
def get_recommendations():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    account = Account.query.filter_by(user_id=user_id).first()
    transactions = Transaction.query.filter_by(account_id=account.id).all() if account else []
    goals = SavingsGoal.query.filter_by(user_id=user_id).all()

    rec_data = generate_savings_recommendations(user, account, transactions, goals)
    return jsonify(rec_data)
