import math
import re
from collections import Counter
from database.db import query_all

class DFRRanker:
    """
    Divergence From Randomness (DFR) Ranking Model.
    Uses the InL2 model:
    - Randomness Model: Inverse Document Frequency (In)
    - First Normalization (Document Length): L2
      tfn = tf * log2(1 + c * (avg_l / l))
    - After-effect parameter: Laplace
      score = sum_t [ ( -log2(1/(1 + lambda)) - tfn * log2(lambda/(1 + lambda)) ) * ( (tfn + 1) / (tfn + 1) ) ]
    """

    def __init__(self, documents=None, c_param: float = 1.0):
        if documents is not None:
            self.docs = documents
        else:
            self.docs = query_all("SELECT doc_id, title, category, content FROM documents")
            
        self.c = c_param
        self.doc_word_counts = {}
        self.doc_lengths = {}
        self.doc_freqs = Counter() # df: number of docs containing term
        self.coll_term_freqs = Counter() # F: total term freq across collection
        self.num_docs = len(self.docs)
        self.total_tokens = 0
        self.avg_doc_len = 0.0

        self._index()

    def _tokenize(self, text: str):
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def _index(self):
        for doc in self.docs:
            d_id = doc["doc_id"]
            tokens = self._tokenize(doc["title"] + " " + doc["content"])
            counts = Counter(tokens)
            self.doc_word_counts[d_id] = counts
            self.doc_lengths[d_id] = len(tokens)
            self.total_tokens += len(tokens)

            for term in counts.keys():
                self.doc_freqs[term] += 1
            for term, count in counts.items():
                self.coll_term_freqs[term] += count

        self.avg_doc_len = (self.total_tokens / self.num_docs) if self.num_docs > 0 else 1.0

    def rank(self, query: str):
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        results = []
        N = max(1, self.num_docs)
        avg_l = max(1.0, self.avg_doc_len)

        for doc in self.docs:
            d_id = doc["doc_id"]
            l = max(1, self.doc_lengths.get(d_id, 1))
            doc_counts = self.doc_word_counts[d_id]
            total_dfr_score = 0.0
            term_breakdown = []

            for t in query_terms:
                tf = doc_counts.get(t, 0)
                if tf == 0:
                    continue

                df = self.doc_freqs.get(t, 1)
                F = self.coll_term_freqs.get(t, 1)

                # Length normalization L2: tfn = tf * log2(1 + c * avg_l / l)
                tfn = tf * math.log2(1.0 + self.c * (avg_l / l))
                
                # lambda = F / N (mean term frequency per document)
                lambda_val = max(1e-6, F / N)

                # Info_1: -log2(P_1) using Poisson / Geometric approximation
                # -log2(1 / (1 + lambda)) - tfn * log2(lambda / (1 + lambda))
                part1 = math.log2(1.0 + lambda_val)
                part2 = tfn * math.log2((1.0 + lambda_val) / lambda_val)
                info1 = part1 + part2

                # Info_2: after-effect normalization
                info2 = (tfn + 1.0) / (tfn + 1.0) # standard InL2 scaling factor

                term_score = info1 * (tfn / (tfn + 1.0))
                total_dfr_score += term_score

                term_breakdown.append({
                    "term": t,
                    "tf": tf,
                    "df": df,
                    "tfn": round(tfn, 3),
                    "lambda": round(lambda_val, 4),
                    "term_score": round(term_score, 4)
                })

            if total_dfr_score > 0:
                results.append({
                    "doc_id": d_id,
                    "title": doc["title"],
                    "category": doc["category"],
                    "content_preview": doc["content"][:160] + "...",
                    "score": round(total_dfr_score, 4),
                    "term_breakdown": term_breakdown
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        for idx, item in enumerate(results):
            item["rank"] = idx + 1

        return results
