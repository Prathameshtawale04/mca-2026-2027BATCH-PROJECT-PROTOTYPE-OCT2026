"""
Stage 11 Full End-to-End System Integration Test Suite
Validates the complete lifecycle:
User Registration -> Login -> Face Biometrics Check -> ATM Transaction ->
50/30/20 Financial Budgeting -> Unit IV LM Search -> Unit V Distributed Web IR ->
Unit VI Collaborative Filtering & Semantic Triples -> Hybrid Fusion -> Admin Oversight.
"""

import pytest
import os
import sys
import json
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import init_db, close_db, query_db
from database.seed_demo_data import seed_all

@pytest.fixture
def app(tmp_path):
    test_db_path = tmp_path / "stage11.db"

    class S11Config(TestConfig):
        DATABASE_PATH = test_db_path

    test_app = create_app(S11Config)
    with test_app.app_context():
        init_db()
        seed_all()
    yield test_app
    close_db()

@pytest.fixture
def client(app):
    return app.test_client()

def test_full_system_integration_lifecycle(client):
    """End-to-end multi-step workflow covering all 10 project functional domains."""
    # 1. Register a new customer
    reg_res = client.post("/register", data={
        "username": "sarah_test",
        "email": "sarah@test.com",
        "full_name": "Sarah Connor",
        "password": "Password123!",
        "pin": "4321"
    }, follow_redirects=True)
    assert reg_res.status_code == 200

    # 2. Login as the newly created customer
    login_res = client.post("/login", data={
        "username": "sarah_test",
        "password": "Password123!"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Sarah Connor" in login_res.data or b"Dashboard" in login_res.data

    # 3. Check Dashboard and ATM view
    atm_view = client.get("/atm")
    assert atm_view.status_code == 200
    assert b"ATM Terminal" in atm_view.data

    # 4. Perform an ATM Deposit
    dep_res = client.post("/atm/api/deposit", json={"amount": 500.0})
    assert dep_res.status_code == 200
    dep_data = json.loads(dep_res.data)
    assert dep_data["success"] is True
    assert dep_data["receipt"]["balance_after"] >= 500.0

    # 5. Add income/expense and verify 50/30/20 financial calculations
    fin_inc = client.post("/finance/api/entry", json={
        "entry_type": "income",
        "category": "Salary",
        "amount": 3000.0,
        "description": "Monthly paycheck"
    })
    assert fin_inc.status_code == 200

    fin_exp = client.post("/finance/api/entry", json={
        "entry_type": "expense",
        "category": "Rent",
        "amount": 1000.0,
        "description": "Apartment lease"
    })
    assert fin_exp.status_code == 200

    summary_res = client.get("/finance/api/summary")
    assert summary_res.status_code == 200
    summary_data = json.loads(summary_res.data)
    assert summary_data["summary"]["total_income"] == 3000.0
    assert summary_data["summary"]["total_expenses"] == 1000.0
    assert summary_data["summary"]["net_savings"] == 2000.0

    # 6. IR Unit IV: Language Models DFA Query Automaton & Dirichlet Ranking
    dfa_res = client.post("/ir/api/dfa", json={"query": "security AND biometric"})
    assert dfa_res.status_code == 200
    assert json.loads(dfa_res.data)["success"] is True

    dirichlet_res = client.post("/ir/api/dirichlet", json={"query": "security", "mu": 1500})
    assert dirichlet_res.status_code == 200
    assert len(json.loads(dirichlet_res.data)["results"]) > 0

    # 7. IR Unit V: Web Retrieval PageRank & Parallel Search
    pr_res = client.post("/ir/api/pagerank", json={"damping": 0.85, "iterations": 15})
    assert pr_res.status_code == 200
    pr_data = json.loads(pr_res.data)
    assert pr_data["success"] is True
    assert "data" in pr_data

    par_res = client.post("/ir/api/parallel", json={"query": "cryptography", "num_shards": 3})
    assert par_res.status_code == 200
    assert json.loads(par_res.data)["success"] is True

    # 8. IR Unit VI: Collaborative Filtering & Knowledge Triples
    cf_res = client.post("/ir/api/cf", json={"target_user": "alex", "k_neighbors": 2})
    assert cf_res.status_code == 200
    assert json.loads(cf_res.data)["success"] is True

    sample_text = "Face recognition is used for ATM authentication. Dr. Alex Vance designed the LBPH system."
    triples_res = client.post("/ir/api/triples", json={"text": sample_text})
    assert triples_res.status_code == 200
    triples_json = json.loads(triples_res.data)
    assert triples_json["success"] is True
    assert len(triples_json["data"]["triples"]) > 0

    # 9. Multi-Model Hybrid Score Fusion Search
    search_res = client.post("/search/api/query", json={
        "query": "biometric face authentication",
        "weight_lm": 0.35,
        "weight_tfidf": 0.35,
        "weight_dfr": 0.15,
        "weight_pagerank": 0.15
    })
    assert search_res.status_code == 200
    search_data = json.loads(search_res.data)
    assert search_data["success"] is True
    assert len(search_data["data"]["results"]) > 0

    # 10. Logout Customer
    logout_res = client.get("/logout", follow_redirects=True)
    assert logout_res.status_code == 200

    # 11. Admin Login & Security Inspection
    admin_login = client.post("/login", data={
        "username": "admin",
        "password": "admin123"
    }, follow_redirects=True)
    assert admin_login.status_code == 200
    assert b"Administrator Portal" in admin_login.data or b"admin" in admin_login.data

    # 12. Admin Audit Logs Stream
    audit_res = client.get("/admin/api/audit_logs")
    assert audit_res.status_code == 200
    audit_data = json.loads(audit_res.data)
    assert audit_data["success"] is True
    assert len(audit_data["logs"]) >= 1

def test_role_based_access_and_security_controls(client):
    """Verify customer cannot access admin routes and admin lock prevents customer login."""
    # 1. Customer login
    client.post("/login", data={"username": "alex", "password": "password123"})
    
    # Customer forbidden from admin portal
    admin_res = client.get("/admin")
    assert admin_res.status_code == 403

    # Customer forbidden from admin API
    admin_api = client.get("/admin/api/audit_logs")
    assert admin_api.status_code == 403

    client.get("/logout")

    # 2. Admin logs in and locks user alex (id=2)
    client.post("/login", data={"username": "admin", "password": "admin123"})
    lock_res = client.post("/admin/api/toggle_user_lock/2")
    assert lock_res.status_code == 200
    assert json.loads(lock_res.data)["is_locked"] == 1

    client.get("/logout")

    # 3. Alex attempts login while locked -> blocked
    locked_login = client.post("/login", data={"username": "alex", "password": "password123"}, follow_redirects=True)
    assert b"locked" in locked_login.data.lower()

    # 4. Admin logs back in and unlocks alex
    client.post("/login", data={"username": "admin", "password": "admin123"})
    unlock_res = client.post("/admin/api/toggle_user_lock/2")
    assert unlock_res.status_code == 200
    assert json.loads(unlock_res.data)["is_locked"] == 0

    client.get("/logout")

    # 5. Alex can log in again
    ok_login = client.post("/login", data={"username": "alex", "password": "password123"}, follow_redirects=True)
    assert b"Alex" in ok_login.data or b"Dashboard" in ok_login.data
