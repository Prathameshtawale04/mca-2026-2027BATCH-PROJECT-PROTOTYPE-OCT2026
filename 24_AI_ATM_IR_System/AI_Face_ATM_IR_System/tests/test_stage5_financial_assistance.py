"""Stage 5: Personal Financial Assistance & 50/30/20 Budgeting Test Suite."""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import init_db, close_db, query_db
from database.seed_demo_data import seed_all
from services.finance_service import (
    add_finance_entry,
    calculate_50_30_20_summary,
    create_savings_goal,
    deposit_into_goal,
    delete_savings_goal
)

@pytest.fixture
def app():
    """Create test application configured with isolated test database."""
    test_db_path = Path(__file__).resolve().parent.parent / "data" / "test_atm_system.db"
    close_db()
    if test_db_path.exists():
        try:
            os.remove(test_db_path)
        except Exception:
            pass
    
    test_app = create_app(TestConfig)
    with test_app.app_context():
        init_db()
        seed_all()
    yield test_app

    close_db()
    if test_db_path.exists():
        try:
            os.remove(test_db_path)
        except Exception:
            pass

@pytest.fixture
def client(app):
    """Test HTTP client with authenticated customer session (Alex Vance, ID: 2)."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alex"
        sess["role"] = "customer"
        sess["full_name"] = "Dr. Alex Vance"
        sess["account_number"] = "ACC1001"
        sess["balance"] = 4850.0
    return c

def test_add_finance_entries(app):
    """Test valid and invalid finance entries logging."""
    with app.app_context():
        # Valid Income
        ok, msg, inc = add_finance_entry(2, "INCOME", "Consulting", 1200.0, description="Tech consulting honorarium")
        assert ok is True
        assert inc["amount"] == 1200.0

        # Valid Expense
        ok, msg, exp = add_finance_entry(2, "EXPENSE", "Groceries", 150.0, description="Fresh produce")
        assert ok is True
        assert exp["category"] == "Groceries"

        # Invalid amount
        ok, msg, _ = add_finance_entry(2, "EXPENSE", "Shopping", -50.0)
        assert ok is False
        assert "positive" in msg.lower()

        # Invalid entry type
        ok, msg, _ = add_finance_entry(2, "TRANSFER", "General", 100.0)
        assert ok is False

def test_50_30_20_calculation_and_guidance(app):
    """Test 50/30/20 mathematical allocation and rule-based guidance output."""
    with app.app_context():
        summary = calculate_50_30_20_summary(2)
        assert summary["total_income"] >= 4500.0
        assert summary["targets"]["needs"] == summary["total_income"] * 0.50
        assert summary["targets"]["wants"] == summary["total_income"] * 0.30
        assert summary["targets"]["savings"] == summary["total_income"] * 0.20

        # Guidance tips must be present and contain educational rules
        assert len(summary["guidance_tips"]) >= 2
        assert any("50%" in t or "Needs" in t for t in summary["guidance_tips"])
        assert "Educational financial simulation only" in summary["disclaimer"]

def test_savings_goals_lifecycle(app):
    """Test savings goal creation, contribution, and auto-completion."""
    with app.app_context():
        # 1. Create Goal
        ok, msg, goal = create_savings_goal(2, "Laptop Vault", 1500.0, "2026-11-30")
        assert ok is True
        gid = goal["id"]
        assert goal["current_amount"] == 0.0
        assert goal["status"] == "IN_PROGRESS"

        # 2. Deposit into Goal
        ok, msg, updated = deposit_into_goal(2, gid, 500.0)
        assert ok is True
        assert updated["current_amount"] == 500.0
        assert updated["status"] == "IN_PROGRESS"

        # 3. Complete Goal by depositing remaining balance
        ok, msg, completed = deposit_into_goal(2, gid, 1000.0)
        assert ok is True
        assert completed["current_amount"] == 1500.0
        assert completed["status"] == "COMPLETED"

        # 4. Delete Goal
        ok, msg = delete_savings_goal(2, gid)
        assert ok is True

def test_finance_api_endpoints(client):
    """Test /finance/api/summary, /finance/api/entry, and /finance/api/goal."""
    # Summary API
    res_sum = client.get("/finance/api/summary")
    assert res_sum.status_code == 200
    assert res_sum.get_json()["summary"]["total_income"] >= 4500.0

    # Add Entry API
    res_ent = client.post("/finance/api/entry", json={
        "entry_type": "EXPENSE",
        "category": "Dining Out",
        "amount": 75.50,
        "description": "Lunch meeting"
    })
    assert res_ent.status_code == 200
    assert res_ent.get_json()["success"] is True

    # Add Goal API
    res_goal = client.post("/finance/api/goal", json={
        "goal_name": "Emergency Cushion",
        "target_amount": 2500.0
    })
    assert res_goal.status_code == 200
    gid = res_goal.get_json()["goal"]["id"]

    # Goal Deposit API
    res_dep = client.post(f"/finance/api/goal/{gid}/deposit", json={"amount": 200.0})
    assert res_dep.status_code == 200
    assert res_dep.get_json()["goal"]["current_amount"] == 200.0

    # Delete Goal API
    res_del = client.delete(f"/finance/api/goal/{gid}")
    assert res_del.status_code == 200
    assert res_del.get_json()["success"] is True
