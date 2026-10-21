import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from datetime import datetime
from models.database import db, User, Account, ChatInteraction
from services.mira_agent import generate_mira_response

mira_bp = Blueprint("mira", __name__, url_prefix="/api/mira")

@mira_bp.route("/chat", methods=["POST"])
def chat():
    # Attempt to retrieve JWT if present, otherwise handle guest
    user_id = None
    user = None
    account = None
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            user_id = int(identity)
            user = User.query.get(user_id)
            account = Account.query.filter_by(user_id=user_id).first()
        else:
            from flask import session as flask_sess
            acc_num = flask_sess.get("account_number")
            if acc_num:
                account = Account.query.filter_by(account_number=acc_num).first()
                if account:
                    user = User.query.get(account.user_id)
                if not user:
                    user = User.query.filter_by(username="alex").first()
                    if user and not account:
                        account = Account.query.filter_by(user_id=user.id).first()
    except Exception:
        pass

    data = request.get_json() or {}
    message = data.get("message", "").strip()
    session_id = data.get("session_id", "guest_session")
    algorithm = data.get("algorithm", "bm25")

    if not message:
        return jsonify({"error": "Empty message"}), 400

    # Save user message
    user_chat = ChatInteraction(
        user_id=user_id,
        session_id=session_id,
        message=message,
        sender="user",
        timestamp=datetime.utcnow()
    )
    db.session.add(user_chat)

    # Generate response via Mira Agent
    response_data = generate_mira_response(user, account, message, ir_algorithm=algorithm)

    # Save agent response
    agent_chat = ChatInteraction(
        user_id=user_id,
        session_id=session_id,
        message=response_data["reply"],
        sender="mira",
        intent=response_data["intent"],
        retrieved_docs=json.dumps(response_data.get("retrieved_docs", [])),
        timestamp=datetime.utcnow()
    )
    db.session.add(agent_chat)
    db.session.commit()

    return jsonify({
        "success": True,
        "reply": response_data["reply"],
        "response": response_data["reply"],
        "intent": response_data["intent"],
        "retrieved_docs": response_data["retrieved_docs"],
        "quick_actions": response_data["quick_actions"],
        "session_id": session_id
    })


@mira_bp.route("/history", methods=["GET"])
def history():
    session_id = request.args.get("session_id", "guest_session")
    chats = ChatInteraction.query.filter_by(session_id=session_id)\
                                 .order_by(ChatInteraction.timestamp.asc())\
                                 .limit(100).all()

    return jsonify({"history": [c.to_dict() for c in chats]})


@mira_bp.route("/clear", methods=["POST"])
def clear_history():
    session_id = request.json.get("session_id", "guest_session") if request.json else "guest_session"
    ChatInteraction.query.filter_by(session_id=session_id).delete()
    db.session.commit()
    return jsonify({"message": "Conversation history cleared"})
