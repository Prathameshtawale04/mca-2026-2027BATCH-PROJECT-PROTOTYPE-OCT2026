"""Stage 6: Information Retrieval Unit IV - Language Models & Ranking Test Suite."""

import pytest
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from config import TestConfig
from database.db import init_db, close_db
from database.seed_demo_data import seed_all

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

def test_language_models_page_access(client):
    """Ensure /ir/language-models page renders with academic documents corpus."""
    res = client.get("/ir/language-models")
    assert res.status_code == 200
    assert b"Unit IV: Language Models" in res.data or b"Deterministic Finite Automaton" in res.data
    assert b"Dirichlet" in res.data
    assert b"DFR" in res.data

def test_api_dfa_query_automaton(client):
    """Verify DFA validates accepted and rejected Boolean queries."""
    # Accepted query
    res = client.post("/ir/api/dfa", json={"query": "face AND recognition"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["result"]["accepted"] is True
    assert "ACCEPT" in data["result"]["states_traversed"]

    # Rejected query
    res_bad = client.post("/ir/api/dfa", json={"query": "AND OR biometric"})
    assert res_bad.status_code == 200
    data_bad = res_bad.get_json()
    assert data_bad["success"] is True
    assert data_bad["result"]["accepted"] is False

    # Empty payload error
    res_empty = client.post("/ir/api/dfa", json={"query": ""})
    assert res_empty.status_code == 400

def test_api_ngram_probabilities_and_perplexity(client):
    """Verify N-gram model evaluates perplexity and token probabilities."""
    res = client.post("/ir/api/ngram", json={"sentence": "Biometric ATM security uses face recognition."})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "unigram" in data["result"]
    assert "bigram" in data["result"]
    assert "trigram" in data["result"]
    assert data["result"]["unigram"]["perplexity"] > 0
    assert data["result"]["bigram"]["perplexity"] > 0

    # Empty payload check
    res_err = client.post("/ir/api/ngram", json={"sentence": ""})
    assert res_err.status_code == 400

def test_api_dirichlet_language_model_ranking(client):
    """Verify Query Likelihood Dirichlet smoothing returns ranked documents."""
    res = client.post("/ir/api/dirichlet", json={"query": "face recognition ATM security", "mu": 2000.0})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["results"]) > 0
    # Results should have title, doc_id, and calculated score
    top = data["results"][0]
    assert "doc_id" in top
    assert "score" in top
    assert "title" in top

    # Empty query check
    res_empty = client.post("/ir/api/dirichlet", json={"query": ""})
    assert res_empty.status_code == 400

def test_api_dfr_ranking(client):
    """Verify Divergence From Randomness (DFR InL2) ranking returns scores."""
    res = client.post("/ir/api/dfr", json={"query": "biometric pin authentication"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["results"]) > 0
    top = data["results"][0]
    assert "score" in top
    assert top["score"] > 0

    # Empty query check
    res_empty = client.post("/ir/api/dfr", json={"query": ""})
    assert res_empty.status_code == 400

def test_api_passage_retriever(client):
    """Verify sliding window passage retrieval extracts relevant highlighted segments."""
    res = client.post("/ir/api/passages", json={"query": "How does face recognition authenticate an ATM user?"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert len(data["results"]) > 0
    top_p = data["results"][0]
    assert "highlighted_text" in top_p
    assert "score" in top_p

    # Empty query check
    res_empty = client.post("/ir/api/passages", json={"query": ""})
    assert res_empty.status_code == 400
