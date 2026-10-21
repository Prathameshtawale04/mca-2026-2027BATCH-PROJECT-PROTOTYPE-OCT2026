import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integrated_search.hybrid_search import IntelligentIRSearch

def test_intelligent_ir_search():
    searcher = IntelligentIRSearch()
    res = searcher.search("face recognition ATM biometric security")
    
    assert res["query"] == "face recognition ATM biometric security"
    assert "automaton_analysis" in res
    assert len(res["results"]) > 0
    
    top_hit = res["results"][0]
    assert "scores" in top_hit
    assert "composite" in top_hit["scores"]
    assert "relevant_passage" in top_hit
    
    # Check post-search recommendations
    assert len(res["post_search_recommendations"]) > 0
    assert "reason" in res["post_search_recommendations"][0]
