from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    pin_hash = db.Column(db.String(256), nullable=True)  # ATM 4-6 digit numeric PIN
    full_name = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="customer")  # 'customer' or 'admin'
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_frozen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    accounts = db.relationship("Account", backref="user", cascade="all, delete-orphan", lazy=True)
    face_template = db.relationship("FaceTemplate", backref="user", uselist=False, cascade="all, delete-orphan")
    savings_goals = db.relationship("SavingsGoal", backref="user", cascade="all, delete-orphan", lazy=True)
    security_events = db.relationship("SecurityEvent", backref="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def set_pin(self, pin: str):
        self.pin_hash = generate_password_hash(str(pin))

    def check_pin(self, pin: str) -> bool:
        if not self.pin_hash:
            return False
        return check_password_hash(self.pin_hash, str(pin))

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "phone": self.phone,
            "is_active": self.is_active,
            "is_frozen": self.is_frozen,
            "has_face_enrolled": self.face_template is not None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Account(db.Model):
    __tablename__ = "accounts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    account_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    account_type = db.Column(db.String(20), default="checking")  # 'checking' or 'savings'
    balance = db.Column(db.Float, default=1000.0)
    daily_limit = db.Column(db.Float, default=2000.0)
    daily_withdrawn_today = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default="active")  # 'active', 'frozen', 'suspended'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    transactions = db.relationship("Transaction", backref="account", cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "account_number": self.account_number,
            "account_type": self.account_type,
            "balance": round(self.balance, 2),
            "daily_limit": round(self.daily_limit, 2),
            "daily_withdrawn_today": round(self.daily_withdrawn_today, 2),
            "remaining_daily_limit": max(0.0, round(self.daily_limit - self.daily_withdrawn_today, 2)),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'deposit', 'withdraw', 'transfer'
    amount = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    recipient_account = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(20), default="completed")  # 'completed', 'flagged', 'blocked', 'reversed'
    fraud_score = db.Column(db.Float, default=0.0)
    is_flagged = db.Column(db.Boolean, default=False)
    flag_reason = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(255), default="")
    channel = db.Column(db.String(20), default="atm")

    def to_dict(self):
        return {
            "id": self.id,
            "account_id": self.account_id,
            "account_number": self.account.account_number if self.account else None,
            "customer_name": self.account.user.full_name if self.account and self.account.user else "Unknown",
            "type": self.type,
            "amount": round(self.amount, 2),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "recipient_account": self.recipient_account,
            "status": self.status,
            "fraud_score": round(self.fraud_score, 3),
            "is_flagged": self.is_flagged,
            "flag_reason": self.flag_reason,
            "description": self.description,
            "channel": self.channel,
        }


class FaceTemplate(db.Model):
    __tablename__ = "face_templates"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    embedding_json = db.Column(db.Text, nullable=False)  # JSON-encoded array of float embeddings
    sample_image_b64 = db.Column(db.Text, nullable=True)  # Snapshot preview of enrolled face
    quality_score = db.Column(db.Float, default=0.95)
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_embedding(self):
        return json.loads(self.embedding_json)

    def set_embedding(self, emb_list):
        self.embedding_json = json.dumps([float(x) for x in emb_list])

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "quality_score": self.quality_score,
            "has_sample": bool(self.sample_image_b64),
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SavingsGoal(db.Model):
    __tablename__ = "savings_goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default="Emergency Fund")
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    target_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="in_progress")  # 'in_progress', 'reached', 'paused'
    auto_save_pct = db.Column(db.Float, default=5.0)  # Suggested auto-save percentage
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        progress = round((self.current_amount / self.target_amount * 100), 1) if self.target_amount > 0 else 0
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "category": self.category,
            "target_amount": round(self.target_amount, 2),
            "current_amount": round(self.current_amount, 2),
            "progress_percentage": min(100.0, progress),
            "remaining_amount": max(0.0, round(self.target_amount - self.current_amount, 2)),
            "target_date": self.target_date.strftime("%Y-%m-%d") if self.target_date else None,
            "status": self.status,
            "auto_save_pct": self.auto_save_pct,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ChatInteraction(db.Model):
    __tablename__ = "chat_interactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user' or 'mira'
    intent = db.Column(db.String(50), nullable=True)
    retrieved_docs = db.Column(db.Text, nullable=True)  # JSON string of retrieved knowledge snippets
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "message": self.message,
            "sender": self.sender,
            "intent": self.intent,
            "retrieved_docs": json.loads(self.retrieved_docs) if self.retrieved_docs else [],
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class SecurityEvent(db.Model):
    __tablename__ = "security_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)
    severity = db.Column(db.String(20), default="medium")  # 'info', 'low', 'medium', 'high', 'critical'
    details = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), default="127.0.0.1")
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    resolved = db.Column(db.Boolean, default=False)
    resolution_note = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else "Anonymous/Guest",
            "event_type": self.event_type,
            "severity": self.severity,
            "details": self.details,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "resolved": self.resolved,
            "resolution_note": self.resolution_note,
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "resource": self.resource,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
