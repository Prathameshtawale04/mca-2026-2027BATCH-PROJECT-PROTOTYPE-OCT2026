import math
from collections import Counter
from database.db import query_all
from web_retrieval.search_engine import MiniSearchEngine

class ContentBasedRecommender:
    """
    Content-Based Filtering Recommender System.
    Builds TF-IDF document profile vectors and computes pairwise Cosine Similarity.
    Recommends resources that share high vocabulary and thematic alignment with the viewed document.
    """

    def __init__(self):
        self.all_docs = query_all("SELECT doc_id, title, category, content FROM documents")
        self.engine = MiniSearchEngine(self.all_docs)

    def recommend_for_document(self, target_doc_id: int, top_k: int = 5):
        target_vec = self.engine.doc_vectors.get(target_doc_id)
        if not target_vec:
            return {"target_doc": None, "recommendations": []}

        target_doc = self.engine.documents[target_doc_id]
        target_norm = target_vec.get("_norm", 1.0)
        target_terms = set(k for k in target_vec.keys() if not k.startswith("_"))

        recommendations = []

        for doc_id, doc in self.engine.documents.items():
            if doc_id == target_doc_id:
                continue

            cand_vec = self.engine.doc_vectors.get(doc_id, {})
            cand_norm = cand_vec.get("_norm", 1.0)

            # Dot product
            common_terms = target_terms.intersection(set(cand_vec.keys()))
            dot = sum(target_vec[t] * cand_vec[t] for t in common_terms)

            if dot > 0 and target_norm > 0 and cand_norm > 0:
                sim = dot / (target_norm * cand_norm)
                top_shared = sorted(
                    common_terms,
                    key=lambda t: target_vec[t] * cand_vec[t],
                    reverse=True
                )[:4]

                recommendations.append({
                    "doc_id": doc_id,
                    "title": doc["title"],
                    "category": doc["category"],
                    "similarity": round(sim, 4),
                    "shared_features": list(top_shared),
                    "reason": f"Matches key themes: {', '.join(top_shared)} (cosine similarity: {sim:.2f})"
                })

        recommendations.sort(key=lambda x: x["similarity"], reverse=True)
        return {
            "target_doc_id": target_doc_id,
            "target_title": target_doc["title"],
            "target_category": target_doc["category"],
            "recommendations": recommendations[:top_k]
        }
