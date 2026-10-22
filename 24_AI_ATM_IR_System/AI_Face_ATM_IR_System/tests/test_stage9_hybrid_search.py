"""Stage 9: Unified Hybrid Search & Telemetry Audit Test Suite."""

import pytest
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import init_db, close_db, query_db
from database.seed_demo_data import seed_all
from services.retrieval_service import execute_hybrid_search, get_user_search_history

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
    """Test HTTP client with authenticated customer session."""
    c = app.test_client()
    with c.session_transaction() as sess:
        sess["user_id"] = 2
        sess["username"] = "alex"
        sess["role"] = "customer"
        sess["full_name"] = "Dr. Alex Vance"
        sess["account_number"] = "ACC1001"
        sess["balance"] = 4850.0
    return c

def test_hybrid_search_page_access(client):
    """Ensure /search/hybrid and /search/history render without error."""
    res_hybrid = client.get("/search/hybrid")
    assert res_hybrid.status_code == 200
    assert b"Unified Hybrid Search Engine" in res_hybrid.data
    assert b"Component Weights" in res_hybrid.data

    res_hist = client.get("/search/history")
    assert res_hist.status_code == 200
    assert b"Search History" in res_hist.data

def test_api_hybrid_search_balanced_weights(client):
    """Verify hybrid search executes multi-model score fusion and returns ranked hits."""
    payload = {
        "query": "biometric face recognition ATM security",
        "w1": 0.40,
        "w2": 0.35,
        "w3": 0.25
    }
    res = client.post("/search/api/query", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    d = data["data"]
    assert d["query"] == payload["query"]
    assert d["total_matches"] > 0
    assert len(d["results"]) > 0

    top = d["results"][0]
    assert "scores" in top
    assert "composite" in top["scores"]
    assert top["scores"]["composite"] > 0
    assert "relevant_passage" in top
    assert "doc_id" in top
    assert "title" in top

def test_api_hybrid_search_custom_weights(client):
    """Verify custom algorithm weighting alters composite scores predictably."""
    res = client.post("/search/api/query", json={
        "query": "PageRank distributed search",
        "w1": 0.80, # High TF-IDF
        "w2": 0.10,
        "w3": 0.10
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["data"]["results"]) > 0

def test_api_hybrid_search_empty_query_validation(client):
    """Verify empty query string returns 400 Bad Request."""
    res = client.post("/search/api/query", json={"query": ""})
    assert res.status_code == 400
    assert res.get_json()["success"] is False

def test_search_history_telemetry_logging(client, app):
    """Verify search queries are recorded in SQLite search_history and retrievable."""
    # Execute two distinct queries
    client.post("/search/api/query", json={"query": "Dirichlet prior smoothing"})
    client.post("/search/api/query", json={"query": "ATM PBKDF2 hash verification"})

    # Check via history API endpoint
    res = client.get("/search/api/history")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    queries = [item["query_text"] for item in data["history"]]
    assert "ATM PBKDF2 hash verification" in queries
    assert "Dirichlet prior smoothing" in queries

    # Check direct database record
    with app.app_context():
        records = query_db("SELECT * FROM search_history WHERE user_id = 2")
        assert len(records) >= 2
        assert records[0]["search_type"] == "HYBRID_FUSION"
        assert records[0]["response_time_ms"] > 0
