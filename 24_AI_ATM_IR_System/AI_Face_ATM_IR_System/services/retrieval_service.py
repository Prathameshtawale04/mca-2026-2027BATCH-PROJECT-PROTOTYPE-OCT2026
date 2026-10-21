"""Hybrid Information Retrieval Service.
Coordinates multi-model score fusion (BM25, Dirichlet Language Model, DFR, PageRank, VSM)
and persists telemetry search audit logs to the SQLite database.
"""

import time
from database.db import execute_sql, query_db
from integrated_search.hybrid_search import IntelligentIRSearch

def execute_hybrid_search(query: str, weights: dict = None, user_id: int = None, account_number: str = None, top_k: int = 10):
    """
    Executes unified multi-model search fusion across:
      1. BM25 / Vector Space Model (TF-IDF)
      2. Query Likelihood Language Model with Dirichlet Smoothing
      3. Divergence From Randomness (DFR InL2)
      4. PageRank Link Graph Centrality
      5. Automated Boolean Automaton Validation
      6. Sliding Window Passage Snippets

    Parameters:
      query: Query string
      weights: Dict of weights (e.g. {'w_tfidf': 0.4, 'w_lm': 0.35, 'w_dfr': 0.25})
      user_id: Authenticated user ID (optional)
      account_number: Authenticated account number (optional)
      top_k: Max results to return

    Returns:
      Dictionary containing query, weights_used, total_matches, results, and response_time_ms.
    """
    t0 = time.perf_counter()
    searcher = IntelligentIRSearch()
    search_res = searcher.search(query, weights=weights, top_k=top_k)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    # Ensure search_history is recorded with the database's schema
    try:
        execute_sql(
            """
            INSERT INTO search_history (user_id, account_number, query_text, search_type, results_count, response_time_ms)
            VALUES (?, ?, ?, 'HYBRID_FUSION', ?, ?)
            """,
            (user_id, account_number, query, len(search_res["results"]), round(elapsed_ms, 2))
        )
    except Exception:
        pass

    search_res["response_time_ms"] = round(elapsed_ms, 2)
    return search_res

def get_user_search_history(user_id: int, limit: int = 50):
    """Retrieve search telemetry audit records for a given user."""
    return query_db(
        """
        SELECT id, query_text, search_type, results_count, response_time_ms, timestamp
        FROM search_history
        WHERE user_id = ? OR user_id IS NULL
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (user_id, limit)
    )
