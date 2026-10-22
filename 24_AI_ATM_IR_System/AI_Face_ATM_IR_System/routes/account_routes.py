from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models.database import db, User, Account, Transaction, SecurityEvent, AuditLog
from services.fraud_service import assess_transaction_risk

account_bp = Blueprint("account", __name__, url_prefix="/api/account")

@account_bp.route("/details", methods=["GET"])
@jwt_required()
def get_details():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    account = Account.query.filter_by(user_id=user.id).first()

    if not account:
        return jsonify({"error": "No account associated with user"}), 404

    return jsonify({
        "account": account.to_dict(),
        "user": user.to_dict()
    })


@account_bp.route("/withdraw", methods=["POST"])
@jwt_required()
def withdraw():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    account = Account.query.filter_by(user_id=user.id).first()

    if not account:
        return jsonify({"error": "Account not found"}), 404

    if user.is_frozen or account.status == "frozen":
        return jsonify({"error": "Account is FROZEN. All withdrawals are locked."}), 403

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Withdrawal amount must be greater than $0"}), 400

    if amount > 800.0:
        return jsonify({"error": "Single transaction ATM withdrawal limit is $800.00"}), 400

    if amount > account.balance:
        return jsonify({"error": f"Insufficient funds. Current balance: ${account.balance:,.2f}"}), 400

    # Daily withdrawal limit check
    remaining_limit = account.daily_limit - account.daily_withdrawn_today
    if amount > remaining_limit:
        return jsonify({
            "error": f"Daily limit exceeded. You have ${remaining_limit:,.2f} remaining out of ${account.daily_limit:,.2f} today."
        }), 400

    # Fetch recent transactions for ML feature extraction
    recent_txs = Transaction.query.filter_by(account_id=account.id)\
                                  .order_by(Transaction.timestamp.desc())\
                                  .limit(20).all()

    # Real-time ML Fraud Risk Assessment
    risk_assessment = assess_transaction_risk(
        amount=amount,
        current_balance=account.balance,
        recent_transactions=recent_txs,
        tx_type="withdraw"
    )

    is_flagged = risk_assessment["is_flagged"]
    fraud_score = risk_assessment["fraud_score"]
    flag_reasons = "; ".join(risk_assessment["flag_reasons"]) if is_flagged else None

    # If critical risk, hold or flag transaction
    tx_status = "flagged" if is_flagged else "completed"

    # Deduct funds
    account.balance -= amount
    account.daily_withdrawn_today += amount

    # Record Transaction
    tx = Transaction(
        account_id=account.id,
        type="withdraw",
        amount=amount,
        status=tx_status,
        fraud_score=fraud_score,
        is_flagged=is_flagged,
        flag_reason=flag_reasons,
        description=f"ATM Cash Dispense ${amount:.2f}",
        channel="atm"
    )
    db.session.add(tx)

    # Log security event if flagged
    if is_flagged:
        sec_event = SecurityEvent(
            user_id=user.id,
            event_type="suspicious_withdrawal",
            severity="high" if fraud_score >= 0.75 else "medium",
            details=f"Withdrawal of ${amount:.2f} flagged. Fraud score: {fraud_score:.3f}. Reasons: {flag_reasons}"
        )
        db.session.add(sec_event)

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="ATM_WITHDRAWAL",
        resource="account",
        details=f"Withdrawal: ${amount:.2f}, Status: {tx_status}, Score: {fraud_score:.3f}"
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        "message": "Cash dispensed successfully" if not is_flagged else "Cash dispensed; transaction flagged for safety review",
        "dispensed_amount": amount,
        "new_balance": round(account.balance, 2),
        "transaction": tx.to_dict(),
        "risk_assessment": risk_assessment
    })


@account_bp.route("/deposit", methods=["POST"])
@jwt_required()
def deposit():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    account = Account.query.filter_by(user_id=user.id).first()

    if not account:
        return jsonify({"error": "Account not found"}), 404

    if user.is_frozen or account.status == "frozen":
        return jsonify({"error": "Account is FROZEN. Cash deposit suspended."}), 403

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Deposit amount must be greater than $0"}), 400

    account.balance += amount

    tx = Transaction(
        account_id=account.id,
        type="deposit",
        amount=amount,
        status="completed",
        fraud_score=0.01,
        is_flagged=False,
        description=f"Optical Cash Deposit ${amount:.2f}",
        channel="atm"
    )
    db.session.add(tx)

    audit = AuditLog(user_id=user.id, action="ATM_DEPOSIT", resource="account", details=f"Cash Deposit: ${amount:.2f}")
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        "message": f"Successfully deposited ${amount:,.2f} into account {account.account_number}",
        "new_balance": round(account.balance, 2),
        "transaction": tx.to_dict()
    })


@account_bp.route("/transfer", methods=["POST"])
@jwt_required()
def transfer():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    source_acc = Account.query.filter_by(user_id=user.id).first()

    if not source_acc:
        return jsonify({"error": "Source account not found"}), 404

    if user.is_frozen or source_acc.status == "frozen":
        return jsonify({"error": "Account is frozen"}), 403

    data = request.get_json() or {}
    recipient_num = data.get("recipient_account", "").strip()
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Transfer amount must be positive"}), 400

    if amount > source_acc.balance:
        return jsonify({"error": "Insufficient funds for transfer"}), 400

    target_acc = Account.query.filter_by(account_number=recipient_num).first()
    if not target_acc:
        return jsonify({"error": f"Recipient account '{recipient_num}' does not exist"}), 404

    if target_acc.id == source_acc.id:
        return jsonify({"error": "Cannot transfer funds to the same account"}), 400

    # Transfer funds
    source_acc.balance -= amount
    target_acc.balance += amount

    # Source transaction
    tx_out = Transaction(
        account_id=source_acc.id,
        type="transfer",
        amount=amount,
        recipient_account=recipient_num,
        status="completed",
        fraud_score=0.05,
        is_flagged=False,
        description=f"Outgoing transfer to {target_acc.user.full_name} ({recipient_num})",
        channel="atm"
    )
    # Target transaction
    tx_in = Transaction(
        account_id=target_acc.id,
        type="deposit",
        amount=amount,
        recipient_account=source_acc.account_number,
        status="completed",
        fraud_score=0.05,
        is_flagged=False,
        description=f"Incoming transfer from {user.full_name}",
        channel="atm"
    )
    db.session.add(tx_out)
    db.session.add(tx_in)

    audit = AuditLog(
        user_id=user.id,
        action="TRANSFER_FUNDS",
        resource="account",
        details=f"Transferred ${amount:.2f} to {recipient_num}"
    )
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        "message": f"Successfully transferred ${amount:,.2f} to {target_acc.user.full_name}",
        "new_balance": round(source_acc.balance, 2),
        "transaction": tx_out.to_dict()
    })


@account_bp.route("/freeze", methods=["POST"])
@jwt_required()
def toggle_freeze():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    account = Account.query.filter_by(user_id=user.id).first()

    # Toggle freeze state
    user.is_frozen = not user.is_frozen
    if account:
        account.status = "frozen" if user.is_frozen else "active"

    state_desc = "FROZEN" if user.is_frozen else "UNFROZEN"
    
    event = SecurityEvent(
        user_id=user.id,
        event_type="account_frozen" if user.is_frozen else "account_unfrozen",
        severity="high" if user.is_frozen else "info",
        details=f"User triggered emergency account {state_desc}"
    )
    db.session.add(event)

    audit = AuditLog(user_id=user.id, action=f"ACCOUNT_{state_desc}", resource="account", details=f"Status set to {state_desc}")
    db.session.add(audit)
    db.session.commit()

    return jsonify({
        "message": f"Account has been successfully {state_desc.lower()}",
        "is_frozen": user.is_frozen,
        "account_status": account.status if account else "unknown"
    })


@account_bp.route("/transactions", methods=["GET"])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())
    account = Account.query.filter_by(user_id=user_id).first()
    if not account:
        return jsonify({"transactions": []})

    txs = Transaction.query.filter_by(account_id=account.id)\
                           .order_by(Transaction.timestamp.desc())\
                           .limit(50).all()

    return jsonify({"transactions": [t.to_dict() for t in txs]})
