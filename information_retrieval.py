import json
import math
import re
from collections import Counter
from urllib.parse import urlsplit


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _row_value(row, key, default=None):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def _tokens(url):
    parsed = urlsplit(str(url).lower())
    return TOKEN_PATTERN.findall(
        " ".join((parsed.hostname or "", parsed.path, parsed.query))
    )


def _canonical_url(url):
    parsed = urlsplit(str(url).strip().lower())
    return parsed._replace(path=parsed.path.rstrip("/")).geturl()


def _language_model_analysis(url, history):
    documents = []
    labels = []
    for row in history:
        try:
            result = json.loads(_row_value(row, "result_json", "{}") or "{}")
        except (TypeError, json.JSONDecodeError):
            continue
        label = str((result.get("ml") or {}).get("classification", "")).lower()
        if label not in {"phishing", "legitimate"}:
            continue
        tokens = _tokens(_row_value(row, "url", ""))
        if tokens:
            documents.append(tokens)
            labels.append(label)

    phishing_documents = [doc for doc, label in zip(documents, labels) if label == "phishing"]
    legitimate_documents = [doc for doc, label in zip(documents, labels) if label == "legitimate"]
    if not phishing_documents or not legitimate_documents:
        return {
            "status": "unavailable",
            "message": "Historical scans labeled by both ML classes are required.",
            "training_documents": len(documents),
            "suspicious_terms": [],
        }

    phishing_counts = Counter(token for doc in phishing_documents for token in doc)
    legitimate_counts = Counter(token for doc in legitimate_documents for token in doc)
    vocabulary = set(phishing_counts) | set(legitimate_counts)
    phishing_total = sum(phishing_counts.values())
    legitimate_total = sum(legitimate_counts.values())
    terms = _tokens(url)
    log_odds = math.log((len(phishing_documents) + 1) / (len(legitimate_documents) + 1))
    for token in terms:
        log_odds += math.log(
            (phishing_counts[token] + 1) / (phishing_total + len(vocabulary))
        ) - math.log(
            (legitimate_counts[token] + 1) / (legitimate_total + len(vocabulary))
        )
    score = 1 / (1 + math.exp(-max(-60, min(60, log_odds))))

    term_likelihoods = []
    for token in vocabulary:
        ratio = math.log(
            (phishing_counts[token] + 1) / (phishing_total + len(vocabulary))
        ) - math.log(
            (legitimate_counts[token] + 1) / (legitimate_total + len(vocabulary))
        )
        if ratio > 0:
            term_likelihoods.append((ratio, token))

    return {
        "status": "available",
        "score": round(score, 6),
        "training_documents": len(documents),
        "suspicious_terms": [
            token for _, token in sorted(term_likelihoods, reverse=True)[:5]
        ],
    }


def _pagerank_analysis(url, history):
    nodes = {
        _canonical_url(_row_value(row, "url", ""))
        for row in history
        if _row_value(row, "url", "")
    }
    candidate = _canonical_url(url)
    nodes.add(candidate)
    return {
        "status": "unavailable",
        "message": "Scan history does not contain observed URL-to-URL links, so graph ranking is unavailable.",
        "graph_nodes": len(nodes),
        "graph_edges": 0,
    }


def _similarity_analysis(url, history):
    candidate = _canonical_url(url)
    historical_urls = sorted({
        _canonical_url(_row_value(row, "url", ""))
        for row in history
        if _row_value(row, "url", "")
        and _canonical_url(_row_value(row, "url", "")) != candidate
    })
    if not historical_urls:
        return {
            "status": "unavailable",
            "message": "No other historical URLs are available for comparison.",
            "recommendations": [],
        }

    documents = [_tokens(item) for item in historical_urls] + [_tokens(url)]
    document_frequency = Counter(
        token for document in documents for token in set(document)
    )
    document_count = len(documents)

    def vector(document):
        return {
            token: (count / len(document))
            * (math.log((document_count + 1) / (document_frequency[token] + 1)) + 1)
            for token, count in Counter(document).items()
        } if document else {}

    candidate_vector = vector(documents[-1])
    candidate_norm = math.sqrt(sum(value * value for value in candidate_vector.values()))
    recommendations = []
    for item, document in zip(historical_urls, documents[:-1]):
        item_vector = vector(document)
        item_norm = math.sqrt(sum(value * value for value in item_vector.values()))
        if not candidate_norm or not item_norm:
            continue
        similarity = sum(
            value * item_vector.get(token, 0)
            for token, value in candidate_vector.items()
        ) / (candidate_norm * item_norm)
        if similarity > 0:
            recommendations.append({"url": item, "similarity": round(similarity, 6)})

    recommendations.sort(key=lambda item: item["similarity"], reverse=True)
    return {
        "status": "available",
        "recommendations": recommendations[:3],
    }


def build_ir_analysis(url, history):
    if not history:
        unavailable = {"status": "unavailable", "message": "No scan-history data is available yet."}
        return {
            "status": "unavailable",
            "message": "IR analysis requires completed scan history.",
            "corpus_size": 0,
            "language_model": {**unavailable, "training_documents": 0, "suspicious_terms": []},
            "pagerank": {**unavailable, "graph_nodes": 1, "graph_edges": 0},
            "content_recommendations": {**unavailable, "recommendations": []},
        }

    language = _language_model_analysis(url, history)
    pagerank = _pagerank_analysis(url, history)
    recommendations = _similarity_analysis(url, history)
    available = any(
        item["status"] == "available"
        for item in (language, pagerank, recommendations)
    )
    return {
        "status": "available" if available else "unavailable",
        "message": "IR analysis calculated from historical scans." if available else "More historical scan data is required for IR analysis.",
        "corpus_size": len(history),
        "language_model": language,
        "pagerank": pagerank,
        "content_recommendations": recommendations,
    }