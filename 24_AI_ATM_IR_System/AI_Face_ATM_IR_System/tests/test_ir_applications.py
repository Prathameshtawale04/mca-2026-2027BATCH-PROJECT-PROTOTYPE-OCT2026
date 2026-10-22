import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ir_applications.collaborative_filter import CollaborativeFilter
from ir_applications.content_recommender import ContentBasedRecommender
from ir_applications.knowledge_recommender import KnowledgeBasedRecommender
from ir_applications.text_extractor import InformationExtractor
from ir_applications.knowledge_graph import SemanticKnowledgeGraph

def test_collaborative_filter():
    cf = CollaborativeFilter()
    recs = cf.recommend("User_Alice", top_k=3)
    assert recs["target_user"] == "User_Alice"
    assert "recommendations" in recs

def test_content_recommender():
    rec = ContentBasedRecommender()
    res = rec.recommend_for_document(1, top_k=3)
    assert len(res["recommendations"]) > 0
    assert res["recommendations"][0]["similarity"] > 0

def test_knowledge_recommender():
    kr = KnowledgeBasedRecommender()
    res = kr.recommend({"technology": "Face Recognition", "application": "ATM Banking"})
    assert res["total_matches"] > 0
    assert res["recommendations"][0]["match_percentage"] > 50

def test_information_extractor():
    ie = InformationExtractor()
    sample_text = "Face recognition is used for ATM authentication. Dr. Alex Vance designed the LBPH system."
    analysis = ie.analyze(sample_text)
    assert len(analysis["entities"]["technologies"]) > 0
    assert len(analysis["triples"]) > 0

def test_semantic_knowledge_graph():
    kg = SemanticKnowledgeGraph()
    subgraph = kg.query_subgraph("ATM")
    assert subgraph["entity_count"] > 0
    assert subgraph["relationship_count"] > 0
