import os
import json
import numpy as np
from datetime import datetime, timedelta
from config import Config
from models.database import db, User, Account, Transaction, FaceTemplate, SavingsGoal, SecurityEvent, AuditLog
from flask import Flask

def create_app_for_seed():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

def seed_database():
    app = create_app_for_seed()
    with app.app_context():
        # Ensure database tables exist
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(username="admin").first():
            print("Database already contains seed data. Skipping re-seed.")
            return

        print("Seeding database with initial users, accounts, transactions, and security logs...")

        # 1. Admin User
        admin = User(
            username="admin",
            email="admin@mira-ai-atm.bank",
            full_name="Chief Security Officer",
            role="admin",
            phone="+1 800-555-0100"
        )
        admin.set_password("admin123")
        admin.set_pin("9999")
        db.session.add(admin)

        # 2. Customer 1: Alex Mercer (Primary demo customer)
        alex = User(
            username="alex",
            email="alex.mercer@gmail.com",
            full_name="Alex Mercer",
            role="customer",
            phone="+1 555-0142"
        )
        alex.set_password("password123")
        alex.set_pin("1234")
        db.session.add(alex)
        db.session.flush()

        # Alex's Checking Account
        alex_acc = Account(
            user_id=alex.id,
            account_number="MIRA-1001-4491",
            account_type="checking",
            balance=2840.50,
            daily_limit=2000.0,
            daily_withdrawn_today=60.0,
            status="active"
        )
        db.session.add(alex_acc)
        db.session.flush()

        # Alex's Face Template (Synthetic 128-d calibrated embedding)
        np.random.seed(101)
        simulated_alex_emb = np.random.normal(0.0, 1.0, 128)
        simulated_alex_emb /= np.linalg.norm(simulated_alex_emb)
        face_tpl = FaceTemplate(
            user_id=alex.id,
            quality_score=0.96
        )
        face_tpl.set_embedding(simulated_alex_emb.tolist())
        db.session.add(face_tpl)

        # Alex's Savings Goals
        g1 = SavingsGoal(
            user_id=alex.id,
            title="3-Month Emergency Cushion",
            category="Emergency Fund",
            target_amount=3500.0,
            current_amount=1650.0,
            target_date=datetime.utcnow() + timedelta(days=120),
            auto_save_pct=5.0
        )
        g2 = SavingsGoal(
            user_id=alex.id,
            title="Tokyo Tech & Travel Trip",
            category="Vacation",
            target_amount=2400.0,
            current_amount=820.0,
            target_date=datetime.utcnow() + timedelta(days=180),
            auto_save_pct=10.0
        )
        db.session.add(g1)
        db.session.add(g2)

        # Alex's Transactions
        now = datetime.utcnow()
        txs = [
            Transaction(
                account_id=alex_acc.id,
                type="deposit",
                amount=2000.0,
                status="completed",
                fraud_score=0.01,
                is_flagged=False,
                description="Bi-Weekly Payroll Direct Deposit",
                timestamp=now - timedelta(days=5),
                channel="atm"
            ),
            Transaction(
                account_id=alex_acc.id,
                type="withdraw",
                amount=60.0,
                status="completed",
                fraud_score=0.08,
                is_flagged=False,
                description="ATM Cash Dispense $60.00",
                timestamp=now - timedelta(hours=3),
                channel="atm"
            ),
            Transaction(
                account_id=alex_acc.id,
                type="withdraw",
                amount=120.0,
                status="completed",
                fraud_score=0.12,
                is_flagged=False,
                description="ATM Cash Dispense $120.00",
                timestamp=now - timedelta(days=2),
                channel="atm"
            ),
            Transaction(
                account_id=alex_acc.id,
                type="withdraw",
                amount=750.0,
                status="flagged",
                fraud_score=0.82,
                is_flagged=True,
                flag_reason="High-value withdrawal near terminal threshold during off-hours",
                description="ATM Cash Dispense $750.00 (Flagged for Review)",
                timestamp=now - timedelta(days=1, hours=2),
                channel="atm"
            ),
        ]
        db.session.add_all(txs)

        # 3. Customer 2: Sophia Chen
        sophia = User(
            username="sophia",
            email="sophia.chen@example.org",
            full_name="Sophia Chen",
            role="customer",
            phone="+1 555-0899"
        )
        sophia.set_password("password123")
        sophia.set_pin("5678")
        db.session.add(sophia)
        db.session.flush()

        sophia_acc = Account(
            user_id=sophia.id,
            account_number="MIRA-2002-8812",
            account_type="checking",
            balance=5200.0,
            daily_limit=2000.0,
            status="active"
        )
        db.session.add(sophia_acc)

        # 4. Security Events
        sec_events = [
            SecurityEvent(
                user_id=alex.id,
                event_type="suspicious_withdrawal",
                severity="high",
                details="Withdrawal of $750.00 flagged by ML Ensemble (score: 0.82). Anomaly triggered: unusual hour & amount spike.",
                timestamp=now - timedelta(days=1, hours=2),
                resolved=False
            ),
            SecurityEvent(
                user_id=None,
                event_type="face_mismatch",
                severity="medium",
                details="3 consecutive face recognition failures at ATM #02. Cosine similarity below 0.35.",
                timestamp=now - timedelta(hours=18),
                resolved=True,
                resolution_note="Customer wearing heavy sunglasses and mask; authenticated successfully after removal."
            ),
            SecurityEvent(
                user_id=None,
                event_type="liveness_failed",
                severity="critical",
                details="Screen video replay spoofing detected by Laplacian variance and moiré sensor.",
                timestamp=now - timedelta(hours=6),
                resolved=False
            )
        ]
        db.session.add_all(sec_events)

        # 5. Audit Logs
        audits = [
            AuditLog(user_id=alex.id, action="ENROLL_FACE", resource="biometrics", details="128-d face embedding template enrolled", timestamp=now - timedelta(days=10)),
            AuditLog(user_id=alex.id, action="LOGIN_FACE_BIOMETRIC", resource="auth", details="Face match verified (similarity 0.88)", timestamp=now - timedelta(hours=3)),
            AuditLog(user_id=admin.id, action="ADMIN_SYSTEM_START", resource="system", details="Mira AI Smart ATM Security Engine Online", timestamp=now - timedelta(hours=24)),
        ]
        db.session.add_all(audits)

        db.session.commit()
        print("Successfully seeded Mira AI ATM database!")

if __name__ == "__main__":
    seed_database()
