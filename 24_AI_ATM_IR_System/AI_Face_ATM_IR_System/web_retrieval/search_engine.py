import re
import math
from collections import defaultdict, Counter
from database.db import query_all

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "did", "do", "does", "doing", "don",
    "down", "during", "each", "few", "for", "from", "further", "had", "has",
    "have", "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "s", "same", "she", "should", "so", "some", "such", "t", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they",
    "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "you", "your", "yours", "yourself", "yourselves"
}

class MiniSearchEngine:
    """
    Classical Search Engine Architecture with Inverted Index and Vector Space Model.
    Architecture:
        Collection -> Tokenizer -> Indexer -> Inverted Index -> Query Processor -> TF-IDF Cosine Ranker
    """

    def __init__(self, documents=None):
        if documents is not None:
            self.documents = {d["doc_id"]: d for d in documents}
        else:
            docs = query_all("SELECT doc_id, title, category, content FROM documents")
            self.documents = {d["doc_id"]: d for d in docs}

        # Inverted index: term -> list of (doc_id, tf, positions)
        self.inverted_index = defaultdict(list)
        self.doc_lengths = {}
        self.doc_vectors = {}
        self.doc_frequencies = Counter()
        self.N = len(self.documents)

        self._build_index()

    def tokenize(self, text: str, remove_stopwords: bool = True):
        tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
        if remove_stopwords:
            return [t for t in tokens if t not in STOPWORDS and len(t) > 1]
        return tokens

    def _build_index(self):
        for doc_id, doc in self.documents.items():
            full_text = f"{doc['title']} {doc['content']}"
            tokens = self.tokenize(full_text)
            self.doc_lengths[doc_id] = len(tokens)

            # Positions map: term -> [pos0, pos1, ...]
            term_positions = defaultdict(list)
            for pos, t in enumerate(tokens):
                term_positions[t].append(pos)

            for term, pos_list in term_positions.items():
                tf = len(pos_list)
                self.inverted_index[term].append({
                    "doc_id": doc_id,
                    "tf": tf,
                    "positions": pos_list
                })
                self.doc_frequencies[term] += 1

        # Precompute TF-IDF document vectors and Euclidean norms
        for doc_id, doc in self.documents.items():
            full_text = f"{doc['title']} {doc['content']}"
            tokens = self.tokenize(full_text)
            counts = Counter(tokens)
            vec = {}
            norm_sq = 0.0

            for term, tf in counts.items():
                df = self.doc_frequencies.get(term, 1)
                # Sublinear TF * IDF
                idf = math.log(1.0 + (self.N / df))
                weight = (1.0 + math.log(tf)) * idf
                vec[term] = weight
                norm_sq += weight * weight

            vec["_norm"] = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            self.doc_vectors[doc_id] = vec

    def search(self, query: str, top_k: int = 10):
        query_tokens = self.tokenize(query)
        if not query_tokens:
            return []

        q_counts = Counter(query_tokens)
        q_vec = {}
        q_norm_sq = 0.0

        for term, tf in q_counts.items():
            df = self.doc_frequencies.get(term, 0)
            if df > 0:
                idf = math.log(1.0 + (self.N / df))
                w = (1.0 + math.log(tf)) * idf
                q_vec[term] = w
                q_norm_sq += w * w

        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0

        scores = []
        for doc_id, doc in self.documents.items():
            d_vec = self.doc_vectors.get(doc_id, {})
            d_norm = d_vec.get("_norm", 1.0)

            dot_product = 0.0
            matched_terms = []

            for q_term, q_w in q_vec.items():
                if q_term in d_vec:
                    dot_product += q_w * d_vec[q_term]
                    matched_terms.append(q_term)

            if dot_product > 0:
                cosine_sim = dot_product / (q_norm * d_norm)
                scores.append({
                    "doc_id": doc_id,
                    "title": doc["title"],
                    "category": doc["category"],
                    "content_preview": doc["content"][:160] + "...",
                    "score": round(cosine_sim, 4),
                    "matched_terms": matched_terms
                })

        scores.sort(key=lambda x: x["score"], reverse=True)
        for idx, item in enumerate(scores[:top_k]):
            item["rank"] = idx + 1

        return scores[:top_k]

    def get_index_view(self, search_term: str = None, limit: int = 40):
        """
        Returns structured view of the inverted index for visual inspection.
        """
        rows = []
        items = self.inverted_index.items()
        if search_term:
            items = [item for item in items if search_term.lower() in item[0]]

        sorted_items = sorted(items, key=lambda x: len(x[1]), reverse=True)[:limit]

        for term, postings in sorted_items:
            rows.append({
                "term": term,
                "document_frequency": len(postings),
                "postings": [
                    {"doc_id": p["doc_id"], "tf": p["tf"], "positions": p["positions"][:5]}
                    for p in postings
                ]
            })

        return {
            "total_terms": len(self.inverted_index),
            "total_documents": self.N,
            "terms": rows
        }
