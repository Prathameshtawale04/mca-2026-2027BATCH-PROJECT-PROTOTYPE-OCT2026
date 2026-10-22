"""Stage 7: Information Retrieval Unit V - Web Retrieval & Crawling Test Suite."""

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

def test_web_retrieval_page_access(client):
    """Ensure /ir/web-retrieval renders Unit V tabs and hyperlink topology."""
    res = client.get("/ir/web-retrieval")
    assert res.status_code == 200
    assert b"Unit V: Web Retrieval" in res.data
    assert b"PageRank Link Graph" in res.data
    assert b"MapReduce Framework" in res.data
    assert b"Parallel Query Coordinator" in res.data

def test_api_pagerank_computation(client):
    """Verify PageRank REST API calculates power iteration and stationary distribution."""
    # Test GET
    res_get = client.get("/ir/api/pagerank")
    assert res_get.status_code == 200
    data_get = res_get.get_json()
    assert data_get["success"] is True
    assert "data" in data_get
    results = data_get["data"]["results"]
    assert len(results) > 0
    # Total sum of PageRank scores should equal 1.0
    total_score = sum(r["pagerank_score"] for r in results)
    assert abs(total_score - 1.0) < 1e-4

    # Test POST with custom damping factor
    res_post = client.post("/ir/api/pagerank", json={"damping": 0.90, "max_iter": 50})
    assert res_post.status_code == 200
    data_post = res_post.get_json()
    assert data_post["success"] is True
    assert data_post["damping"] == 0.90

def test_api_mapreduce_pipeline(client):
    """Verify MapReduce pipeline simulation on document corpus."""
    res = client.post("/ir/api/mapreduce")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "report" in data
    rep = data["report"]
    assert rep["total_map_pairs_emitted"] > 0
    assert rep["unique_terms_reduced"] > 0
    assert len(rep["reduced_index"]) > 0
    assert len(rep["sample_postings"]) > 0

def test_api_parallel_query_coordinator(client):
    """Verify parallel query coordinator splits work among shards and aggregates."""
    res = client.post("/ir/api/parallel", json={"query": "face recognition biometrics", "nodes": 3})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "data" in data
    d = data["data"]
    assert d["node_count"] == 3
    assert len(d["node_reports"]) == 3
    # Check that latency was recorded for each node
    for node in d["node_reports"]:
        assert "latency_ms" in node
        assert "docs_in_shard" in node
    assert len(d["final_results"]) > 0

    # Empty query check
    res_empty = client.post("/ir/api/parallel", json={"query": ""})
    assert res_empty.status_code == 400

def test_api_polite_web_crawler(client):
    """Verify polite web crawler visits pages within safe limits."""
    res = client.post("/ir/api/crawl", json={"url": "https://academic-atm.local/security", "depth": 1, "max_pages": 2})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "report" in data
    rep = data["report"]
    assert rep["total_crawled"] >= 1
    assert len(rep["crawled_pages"]) >= 1
    assert rep["crawled_pages"][0]["status_code"] == 200
