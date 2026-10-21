"""Hybrid Search & Query History Routes."""

from flask import Blueprint, render_template, request, jsonify, session
from services.auth_service import login_required
from database.db import query_db
from services.retrieval_service import execute_hybrid_search, get_user_search_history

search_bp = Blueprint("search", __name__, url_prefix="/search")

@search_bp.route("/hybrid")
@login_required
def hybrid_search():
    """Hybrid search workbench with score fusion (BM25 + Dirichlet LM + TF-IDF) and weight sliders."""
    docs = query_db("SELECT * FROM documents ORDER BY doc_id ASC")
    return render_template("search/hybrid.html", docs=docs)

@search_bp.route("/history")
@login_required
def history():
    """Search query audit history and system telemetry reports."""
    user_id = session.get("user_id")
    history_records = get_user_search_history(user_id)
    return render_template("search/history.html", history=history_records)

@search_bp.route("/api/query", methods=["POST"])
@login_required
def api_query():
    """Execute hybrid search with customizable algorithm weights."""
    data = request.get_json(silent=True) or request.form
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Search query required"}), 400

    # Map sliders or weights dict
    weights = {
        "w_tfidf": float(data.get("w1", data.get("w_tfidf", 0.40))),
        "w_lm": float(data.get("w2", data.get("w_lm", 0.35))),
        "w_dfr": float(data.get("w3", data.get("w_dfr", 0.25))),
        "w_pagerank": float(data.get("w_pagerank", 0.15)),
        "w_semantic": float(data.get("w_semantic", 0.15))
    }

    user_id = session.get("user_id")
    account_number = session.get("account_number")

    results = execute_hybrid_search(
        query=query,
        weights=weights,
        user_id=user_id,
        account_number=account_number,
        top_k=10
    )

    return jsonify({"success": True, "data": results})

@search_bp.route("/api/history", methods=["GET"])
@login_required
def api_history():
    """Fetch search query history as JSON."""
    user_id = session.get("user_id")
    records = get_user_search_history(user_id)
    return jsonify({"success": True, "history": [dict(r) for r in records]})
