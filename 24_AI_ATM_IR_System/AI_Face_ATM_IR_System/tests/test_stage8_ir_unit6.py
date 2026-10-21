"""Stage 8: Information Retrieval Unit VI - IR Applications & Semantic Web Test Suite."""

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

def test_ir_applications_page_access(client):
    """Ensure /ir/applications renders Unit VI recommender tabs and RDF knowledge graph."""
    res = client.get("/ir/applications")
    assert res.status_code == 200
    assert b"Unit VI: IR Applications" in res.data
    assert b"Collaborative Filtering" in res.data
    assert b"Content-Based Recommender" in res.data
    assert b"Knowledge-Based Rules" in res.data
    assert b"Semantic Knowledge Graph" in res.data

def test_api_collaborative_filtering(client):
    """Verify Collaborative Filtering returns personalized predictions and utility matrix."""
    res = client.post("/ir/api/cf", json={"user": "User_Alice", "top_k": 3})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "data" in data
    assert "matrix" in data
    assert data["data"]["target_user"] == "User_Alice"
    assert "recommendations" in data["data"]
    assert len(data["matrix"]["users"]) > 0

def test_api_content_based_recommender(client):
    """Verify Content-Based recommender computes cosine similarities across TF-IDF document profiles."""
    res = client.post("/ir/api/cb", json={"doc_id": 1, "top_k": 3})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "data" in data
    d = data["data"]
    assert d["target_doc_id"] == 1
    assert len(d["recommendations"]) > 0
    top = d["recommendations"][0]
    assert "similarity" in top
    assert top["similarity"] > 0
    assert "title" in top

def test_api_knowledge_rules(client):
    """Verify Knowledge-Based rule engine infers relevant articles from multi-attribute criteria."""
    res = client.post("/ir/api/knowledge_rules", json={
        "technology": "Face Recognition",
        "application": "ATM Banking"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "data" in data
    d = data["data"]
    assert d["total_matches"] > 0
    assert len(d["recommendations"]) > 0
    top = d["recommendations"][0]
    assert top["match_percentage"] > 50

def test_api_information_extraction_and_triples(client):
    """Verify InformationExtractor extracts technologies and RDF triples from text."""
    sample = "Face recognition is used for ATM authentication. Dr. Alex Vance designed the LBPH system."
    res = client.post("/ir/api/triples", json={"text": sample})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    d = data["data"]
    assert len(d["entities"]["technologies"]) > 0
    assert len(d["triples"]) > 0
    triple = d["triples"][0]
    assert "subject" in triple
    assert "predicate" in triple
    assert "object" in triple

    # Empty payload validation
    res_empty = client.post("/ir/api/triples", json={"text": ""})
    assert res_empty.status_code == 400

def test_api_semantic_knowledge_subgraph(client):
    """Verify SemanticKnowledgeGraph returns Vis.js nodes, edges, and entity counts."""
    res = client.post("/ir/api/kg_subgraph", json={"query": "ATM"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    d = data["data"]
    assert d["entity_count"] > 0
    assert d["relationship_count"] > 0
    assert "vis_graph" in d
    assert len(d["vis_graph"]["nodes"]) > 0
    assert len(d["vis_graph"]["edges"]) > 0
