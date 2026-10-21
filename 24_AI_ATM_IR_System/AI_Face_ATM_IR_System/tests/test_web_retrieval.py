import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web_retrieval.mapreduce_engine import MapReduceEngine
from web_retrieval.search_engine import MiniSearchEngine
from web_retrieval.pagerank import PageRankEngine
from web_retrieval.parallel_query import ParallelQueryCoordinator
from web_retrieval.beautifulsoup_crawler import AcademicWebCrawler

def test_mapreduce_engine():
    mr = MapReduceEngine()
    docs = [
        {"doc_id": 1, "content": "face recognition biometrics ATM"},
        {"doc_id": 2, "content": "ATM security face recognition"}
    ]
    report = mr.execute(docs)
    assert report["total_map_pairs_emitted"] > 0
    assert report["unique_terms_reduced"] > 0

def test_mini_search_engine():
    engine = MiniSearchEngine()
    results = engine.search("face recognition")
    assert len(results) > 0
    assert results[0]["score"] > 0

def test_pagerank_algorithm():
    pr_engine = PageRankEngine()
    pr_data = pr_engine.compute()
    assert pr_data["converged"] is True
    assert len(pr_data["results"]) > 0
    # Sum of PageRank scores across all nodes should equal 1.0
    total_pr = sum(r["pagerank_score"] for r in pr_data["results"])
    assert abs(total_pr - 1.0) < 1e-4

def test_parallel_query_coordinator():
    coord = ParallelQueryCoordinator(num_nodes=3)
    res = coord.execute_parallel_search("biometric authentication")
    assert res["node_count"] == 3
    assert len(res["final_results"]) > 0

def test_academic_crawler():
    crawler = AcademicWebCrawler(max_depth=1, max_pages=2)
    report = crawler.crawl("https://academic-atm.local/security")
    assert report["total_crawled"] >= 1
    assert len(report["crawled_pages"]) >= 1
