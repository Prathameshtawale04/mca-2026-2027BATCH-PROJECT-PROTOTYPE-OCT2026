import math
import re
from collections import Counter
from database.db import query_all

class LanguageModelRanker:
    """
    Query Likelihood Ranking Model with Jelinek-Mercer and Dirichlet Prior smoothing.
    P(Q|D) = prod( P(q | D) )
    """
    def __init__(self, documents=None):
        if documents is not None:
            self.docs = documents
        else:
            self.docs = query_all("SELECT doc_id, title, category, content FROM documents")
        
        self.doc_word_counts = {}
        self.doc_lengths = {}
        self.collection_counts = Counter()
        self.total_collection_tokens = 0
        
        self._index_collection()

    def _tokenize(self, text: str):
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def _index_collection(self):
        for doc in self.docs:
            d_id = doc["doc_id"]
            tokens = self._tokenize(doc["title"] + " " + doc["content"])
            counts = Counter(tokens)
            self.doc_word_counts[d_id] = counts
            self.doc_lengths[d_id] = len(tokens)
            self.collection_counts.update(counts)
            self.total_collection_tokens += len(tokens)

    def rank(self, query: str, smoothing: str = "dirichlet", mu: float = 1000.0, lambda_param: float = 0.6):
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        results = []
        for doc in self.docs:
            d_id = doc["doc_id"]
            d_len = self.doc_lengths.get(d_id, 0)
            if d_len == 0:
                continue

            doc_counts = self.doc_word_counts[d_id]
            log_score = 0.0
            term_details = []
            matched_terms = []

            for q in query_terms:
                c_qd = doc_counts.get(q, 0)
                p_coll = self.collection_counts.get(q, 0.5) / max(1, self.total_collection_tokens)

                if smoothing == "dirichlet":
                    # P(q|D) = (c(q,D) + mu * P(q|C)) / (|D| + mu)
                    p_qd = (c_qd + mu * p_coll) / (d_len + mu)
                else: # Jelinek-Mercer
                    p_ml = c_qd / d_len
                    p_qd = lambda_param * p_ml + (1.0 - lambda_param) * p_coll

                term_log = math.log(max(p_qd, 1e-12))
                log_score += term_log
                
                if c_qd > 0:
                    matched_terms.append(q)
                
                term_details.append({
                    "term": q,
                    "count_in_doc": c_qd,
                    "p_qd": round(p_qd, 6),
                    "log_prob": round(term_log, 4)
                })

            results.append({
                "doc_id": d_id,
                "title": doc["title"],
                "category": doc["category"],
                "content_preview": doc["content"][:160] + "...",
                "score": round(log_score, 4),
                "matched_terms": list(set(matched_terms)),
                "match_count": len(matched_terms),
                "term_details": term_details
            })

        # Rank descending
        results.sort(key=lambda x: x["score"], reverse=True)
        for idx, item in enumerate(results):
            item["rank"] = idx + 1

        return results
