"""Information Retrieval Academic Routes (Unit IV, Unit V, Unit VI) & Interactive APIs."""

from flask import Blueprint, render_template, request, jsonify
from services.auth_service import login_required
from database.db import query_db

from language_models.query_automaton import QueryAutomaton
from language_models.ngram_models import NGramLanguageModel
from language_models.multinomial_model import MultinomialWordModel
from language_models.lm_ranker import LanguageModelRanker
from language_models.dfr_ranker import DFRRanker
from language_models.passage_retriever import PassageRetriever
from language_models.ir_metrics import IREvaluator

from web_retrieval.pagerank import PageRankEngine
from web_retrieval.mapreduce_engine import MapReduceEngine
from web_retrieval.parallel_query import ParallelQueryCoordinator
from web_retrieval.beautifulsoup_crawler import AcademicWebCrawler
from web_retrieval.search_engine import MiniSearchEngine

from ir_applications.collaborative_filter import CollaborativeFilter
from ir_applications.content_recommender import ContentBasedRecommender
from ir_applications.knowledge_recommender import KnowledgeBasedRecommender
from ir_applications.text_extractor import InformationExtractor
from ir_applications.knowledge_graph import SemanticKnowledgeGraph

ir_bp = Blueprint("ir", __name__, url_prefix="/ir")

@ir_bp.route("/language-models")
@login_required
def language_models():
    """Unit IV: Language Models, DFA Automata, Dirichlet Smoothing, DFR & Passage Retrieval."""
    docs = query_db("SELECT * FROM documents ORDER BY doc_id ASC")
    return render_template("ir/language_models.html", docs=docs)

@ir_bp.route("/web-retrieval")
@login_required
def web_retrieval():
    """Unit V: Web Retrieval, PageRank, MapReduce, Parallel Processing & Crawlers."""
    crawl_pages = query_db("SELECT * FROM crawl_pages ORDER BY id ASC")
    links = query_db("SELECT * FROM links ORDER BY id ASC")
    return render_template("ir/web_retrieval.html", crawl_pages=crawl_pages, links=links)

@ir_bp.route("/applications")
@login_required
def applications():
    """Unit VI: IR Applications, Collaborative Filtering, Content Recommender & Knowledge Graph."""
    triples = query_db("SELECT * FROM knowledge_triples ORDER BY id ASC")
    interactions = query_db("SELECT * FROM user_interactions ORDER BY id ASC")
    documents = query_db("SELECT doc_id, title, category FROM documents ORDER BY doc_id ASC")
    users = query_db("SELECT id, username, full_name, role FROM users ORDER BY id ASC")
    return render_template("ir/applications.html", triples=triples, interactions=interactions, documents=documents, users=users)

# ----------------- Unit IV REST APIs -----------------

@ir_bp.route("/api/dfa", methods=["POST"])
@login_required
def api_dfa():
    """Run Deterministic Finite Automaton (DFA) query parser."""
    data = request.get_json(silent=True) or request.form
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Query string required"}), 400
    qa = QueryAutomaton()
    result = qa.process(query)
    return jsonify({"success": True, "result": result})

@ir_bp.route("/api/ngram", methods=["POST"])
@login_required
def api_ngram():
    """Evaluate N-gram probabilities and perplexity."""
    data = request.get_json(silent=True) or request.form
    sentence = data.get("sentence", "").strip()
    if not sentence:
        return jsonify({"success": False, "message": "Sentence string required"}), 400
    ngram = NGramLanguageModel()
    result = ngram.evaluate_sentence(sentence)
    return jsonify({"success": True, "result": result})

@ir_bp.route("/api/dirichlet", methods=["POST"])
@login_required
def api_dirichlet():
    """Query Likelihood ranking with Dirichlet prior smoothing."""
    data = request.get_json(silent=True) or request.form
    query = data.get("query", "").strip()
    mu = float(data.get("mu", 2000.0))
    if not query:
        return jsonify({"success": False, "message": "Query string required"}), 400
    ranker = LanguageModelRanker()
    ranked = ranker.rank(query, smoothing="dirichlet", mu=mu)
    return jsonify({"success": True, "query": query, "method": "Dirichlet (mu=2000)", "results": ranked})

@ir_bp.route("/api/dfr", methods=["POST"])
@login_required
def api_dfr():
    """Divergence From Randomness (DFR InL2) ranking model."""
    data = request.get_json(silent=True) or request.form
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Query string required"}), 400
    dfr = DFRRanker()
    ranked = dfr.rank(query)
    return jsonify({"success": True, "query": query, "method": "DFR (InL2)", "results": ranked})

@ir_bp.route("/api/passages", methods=["POST"])
@login_required
def api_passages():
    """Sliding window passage retrieval and sentence highlighting."""
    data = request.get_json(silent=True) or request.form
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Query string required"}), 400
    retriever = PassageRetriever()
    passages = retriever.search_passages(query)
    return jsonify({"success": True, "query": query, "results": passages})

# ----------------- Unit V REST APIs -----------------

@ir_bp.route("/api/pagerank", methods=["GET", "POST"])
@login_required
def api_pagerank():
    """Compute PageRank scores over hyperlink graph using power iteration."""
    data = (request.get_json(silent=True) or request.form) if request.method == "POST" else {}
    damping = float(data.get("damping", 0.85))
    max_iter = int(data.get("max_iter", 100))

    # Pull link graph from DB if available
    db_links = query_db("SELECT source_url, target_url FROM links")
    edges = [(row["source_url"], row["target_url"]) for row in db_links] if db_links else None

    pr_engine = PageRankEngine(edges=edges, damping_factor=damping, max_iter=max_iter)
    result = pr_engine.compute()
    return jsonify({"success": True, "damping": damping, "data": result})

@ir_bp.route("/api/mapreduce", methods=["POST"])
@login_required
def api_mapreduce():
    """Simulate MapReduce framework execution on document corpus."""
    docs = query_db("SELECT doc_id, content FROM documents")
    mr = MapReduceEngine()
    report = mr.execute([dict(d) for d in docs])
    report["sample_postings"] = report.get("reduced_index", [])[:15]
    return jsonify({"success": True, "report": report})

@ir_bp.route("/api/parallel", methods=["POST"])
@login_required
def api_parallel():
    """Execute distributed search query across partitioned node shards."""
    data = request.get_json(silent=True) or request.form
    query = data.get("query", "").strip()
    nodes = int(data.get("nodes", 3))
    if not query:
        return jsonify({"success": False, "message": "Query string required"}), 400
    coord = ParallelQueryCoordinator(num_nodes=nodes)
    res = coord.execute_parallel_search(query)
    return jsonify({"success": True, "query": query, "data": res})

@ir_bp.route("/api/crawl", methods=["POST"])
@login_required
def api_crawl():
    """Execute controlled polite web crawler on target URL."""
    data = request.get_json(silent=True) or request.form
    start_url = data.get("url", "https://academic-atm.local/security").strip()
    depth = int(data.get("depth", 1))
    max_pages = int(data.get("max_pages", 3))

    crawler = AcademicWebCrawler(max_depth=depth, max_pages=max_pages)
    report = crawler.crawl(start_url)
    return jsonify({"success": True, "report": report})

# ----------------- Unit VI REST APIs -----------------

@ir_bp.route("/api/cf", methods=["GET", "POST"])
@login_required
def api_cf():
    """User-based Collaborative Filtering recommendations and rating matrix."""
    data = (request.get_json(silent=True) or request.form) if request.method == "POST" else {}
    target_user = data.get("user", "User_Alice").strip()
    top_k = int(data.get("top_k", 5))

    cf = CollaborativeFilter()
    recs = cf.recommend(target_user, top_k=top_k)
    matrix = cf.get_matrix_view()
    return jsonify({"success": True, "data": recs, "matrix": matrix})

@ir_bp.route("/api/cb", methods=["POST"])
@login_required
def api_cb():
    """Content-based TF-IDF cosine recommendations for a selected document."""
    data = request.get_json(silent=True) or request.form
    doc_id = int(data.get("doc_id", 1))
    top_k = int(data.get("top_k", 4))

    cb = ContentBasedRecommender()
    recs = cb.recommend_for_document(doc_id, top_k=top_k)
    return jsonify({"success": True, "data": recs})

@ir_bp.route("/api/knowledge_rules", methods=["POST"])
@login_required
def api_knowledge_rules():
    """Knowledge-based rule inference engine matching user profile constraints."""
    data = request.get_json(silent=True) or request.form
    tech = data.get("technology", "Face Recognition")
    app = data.get("application", "ATM Banking")
    sec = data.get("security_level", "Critical")

    kr = KnowledgeBasedRecommender()
    recs = kr.recommend({"technology": tech, "application": app, "security_level": sec})
    return jsonify({"success": True, "data": recs})

@ir_bp.route("/api/triples", methods=["POST"])
@login_required
def api_triples():
    """Extract RDF entities and (subject, predicate, object) triples from text."""
    data = request.get_json(silent=True) or request.form
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"success": False, "message": "Text payload required"}), 400

    ie = InformationExtractor()
    analysis = ie.analyze(text)
    return jsonify({"success": True, "data": analysis})

@ir_bp.route("/api/kg_subgraph", methods=["GET", "POST"])
@login_required
def api_kg_subgraph():
    """Query semantic RDF knowledge graph for entity subgraphs and Vis.js nodes."""
    data = (request.get_json(silent=True) or request.form) if request.method == "POST" else {}
    query = data.get("query", "").strip() or None

    kg = SemanticKnowledgeGraph()
    subgraph = kg.query_subgraph(query)
    return jsonify({"success": True, "data": subgraph})


