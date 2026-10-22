import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from language_models.query_automaton import QueryAutomaton
from language_models.ngram_models import NGramLanguageModel
from language_models.multinomial_model import MultinomialWordModel
from language_models.lm_ranker import LanguageModelRanker
from language_models.dfr_ranker import DFRRanker
from language_models.passage_retriever import PassageRetriever
from language_models.ir_metrics import IREvaluator

def test_query_automaton():
    qa = QueryAutomaton()
    valid_res = qa.process("face AND recognition")
    assert valid_res["accepted"] is True
    assert "ACCEPT" in valid_res["states_traversed"]

    invalid_res = qa.process("AND OR face")
    assert invalid_res["accepted"] is False

def test_ngram_models():
    ngram = NGramLanguageModel()
    res = ngram.evaluate_sentence("Biometric ATM security uses face recognition.")
    assert "unigram" in res
    assert "bigram" in res
    assert "trigram" in res
    assert res["unigram"]["perplexity"] > 0
    assert res["bigram"]["perplexity"] > 0

def test_multinomial_model():
    m = MultinomialWordModel()
    dist = m.get_distribution(top_k=10)
    assert len(dist["chart_data"]["labels"]) == 10
    assert dist["total_tokens"] > 0

def test_lm_ranker():
    ranker = LanguageModelRanker()
    ranked = ranker.rank("face recognition ATM security")
    assert len(ranked) > 0
    assert ranked[0]["score"] is not None

def test_dfr_ranker():
    dfr = DFRRanker()
    ranked = dfr.rank("face recognition")
    assert len(ranked) > 0
    assert ranked[0]["score"] > 0

def test_passage_retriever():
    retriever = PassageRetriever()
    passages = retriever.search_passages("How does face recognition authenticate an ATM user?")
    assert len(passages) > 0
    assert "highlighted_text" in passages[0]

def test_ir_metrics():
    retrieved = [1, 2, 3, 4, 5]
    relevant = {1, 2, 6}
    metrics = IREvaluator.evaluate_query(retrieved, relevant)
    
    assert metrics["precision"] == 2 / 5
    assert metrics["recall"] == pytest.approx(2 / 3, 0.001)
    assert metrics["p_at_3"] == pytest.approx(2 / 3, 0.001)
    assert metrics["f1_score"] > 0
