import re
import math
from collections import Counter
from database.db import query_all

class PassageRetriever:
    """
    Passage Retrieval Engine.
    Splits long documents into sliding passages of K sentences, computes passage-level
    relevance scores, and highlights query terms.
    """

    def __init__(self, documents=None, window_sentences: int = 2, step_sentences: int = 1):
        if documents is not None:
            self.docs = documents
        else:
            self.docs = query_all("SELECT doc_id, title, category, content FROM documents")
            
        self.window_sentences = window_sentences
        self.step_sentences = step_sentences

    def _split_sentences(self, text: str):
        raw = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in raw if len(s.strip()) > 5]

    def _tokenize(self, text: str):
        return re.findall(r'[a-zA-Z0-9]+', text.lower())

    def create_passages(self, doc):
        sentences = self._split_sentences(doc["content"])
        if not sentences:
            return [{
                "passage_id": f"{doc['doc_id']}_p1",
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "category": doc["category"],
                "text": doc["content"],
                "tokens": self._tokenize(doc["content"])
            }]

        passages = []
        p_idx = 1
        i = 0
        while i < len(sentences):
            chunk = sentences[i : i + self.window_sentences]
            passage_text = " ".join(chunk)
            passages.append({
                "passage_id": f"{doc['doc_id']}_p{p_idx}",
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "category": doc["category"],
                "text": passage_text,
                "tokens": self._tokenize(passage_text)
            })
            p_idx += 1
            i += self.step_sentences
            if i >= len(sentences) and i - self.step_sentences + self.window_sentences >= len(sentences):
                break

        return passages

    def highlight_terms(self, text: str, query_terms: list):
        if not query_terms:
            return text
        escaped_terms = [re.escape(t) for t in set(query_terms) if len(t) > 1]
        if not escaped_terms:
            return text
        pattern = re.compile(r'\b(' + '|'.join(escaped_terms) + r')\b', re.IGNORECASE)
        return pattern.sub(r'<mark class="passage-highlight">\1</mark>', text)

    def search_passages(self, query: str, top_k: int = 10):
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        all_passages = []
        for doc in self.docs:
            all_passages.extend(self.create_passages(doc))

        results = []
        for p in all_passages:
            tokens = p["tokens"]
            if not tokens:
                continue

            passage_counts = Counter(tokens)
            p_len = len(tokens)
            
            # Simple TF-based passage scoring with length penalty
            matched_terms = []
            score = 0.0

            for q in query_terms:
                c = passage_counts.get(q, 0)
                if c > 0:
                    matched_terms.append(q)
                    tf = math.log(1 + c)
                    score += tf

            if score > 0:
                normalized_score = score / (1.0 + 0.1 * math.log(p_len))
                results.append({
                    "passage_id": p["passage_id"],
                    "doc_id": p["doc_id"],
                    "title": p["title"],
                    "category": p["category"],
                    "raw_text": p["text"],
                    "highlighted_text": self.highlight_terms(p["text"], query_terms),
                    "score": round(normalized_score, 4),
                    "matched_terms": list(set(matched_terms)),
                    "match_count": len(matched_terms)
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        for idx, item in enumerate(results[:top_k]):
            item["rank"] = idx + 1

        return results[:top_k]
