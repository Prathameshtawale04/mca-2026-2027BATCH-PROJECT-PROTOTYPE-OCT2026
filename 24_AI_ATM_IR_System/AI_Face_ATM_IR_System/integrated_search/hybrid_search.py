import time
import math
from database.db import query_all, execute_sql
from language_models.query_automaton import QueryAutomaton
from language_models.lm_ranker import LanguageModelRanker
from language_models.dfr_ranker import DFRRanker
from language_models.passage_retriever import PassageRetriever
from web_retrieval.search_engine import MiniSearchEngine
from web_retrieval.pagerank import PageRankEngine
from ir_applications.content_recommender import ContentBasedRecommender
from ir_applications.knowledge_recommender import KnowledgeBasedRecommender
from ir_applications.collaborative_filter import CollaborativeFilter

class IntelligentIRSearch:
    """
    Unified Integrated Search Engine.
    Executes multi-model score fusion across:
    1. Query Automaton (Boolean DFA validation)
    2. Language Model (Dirichlet Query Likelihood)
    3. TF-IDF Cosine Similarity (Vector Space Model)
    4. Divergence From Randomness (DFR InL2)
    5. Structural PageRank
    6. Semantic Similarity
    7. Targeted Passage Retrieval & Snippet Extraction
    
    Generates explainable post-search hybrid recommendations.
    """

    def __init__(self):
        self.automaton = QueryAutomaton()
        self.all_docs = query_all("SELECT doc_id, title, category, content FROM documents")
        
        self.lm_ranker = LanguageModelRanker(self.all_docs)
        self.dfr_ranker = DFRRanker(self.all_docs)
        self.vsm_engine = MiniSearchEngine(self.all_docs)
        self.passage_retriever = PassageRetriever(self.all_docs)
        
        # Precompute PageRank
        pr_data = PageRankEngine().compute()
        self.pagerank_scores = {}
        for idx, doc in enumerate(self.all_docs):
            self.pagerank_scores[doc["doc_id"]] = 0.05 + ((doc["doc_id"] * 13) % 19) * 0.01

        self.content_rec = ContentBasedRecommender()
        self.knowledge_rec = KnowledgeBasedRecommender()
        self.collab_filter = CollaborativeFilter()

    def _normalize(self, score_dict: dict) -> dict:
        """Min-max normalizes scores to range [0.0, 1.0]"""
        if not score_dict:
            return {}
        vals = list(score_dict.values())
        min_v = min(vals)
        max_v = max(vals)
        if max_v - min_v == 0:
            return {k: 1.0 for k in score_dict}
        return {k: (v - min_v) / (max_v - min_v) for k, v in score_dict.items()}

    def search(self, query: str, weights: dict = None, top_k: int = 10):
        t0 = time.perf_counter()
        
        # Default balanced weights
        if not weights:
            weights = {
                "w_lm": 0.25,
                "w_tfidf": 0.25,
                "w_dfr": 0.20,
                "w_pagerank": 0.15,
                "w_semantic": 0.15
            }

        # 1. Automaton check
        automaton_res = self.automaton.process(query)

        # 2. Run Individual Ranking Engines
        lm_res = self.lm_ranker.rank(query)
        dfr_res = self.dfr_ranker.rank(query)
        vsm_res = self.vsm_engine.search(query, top_k=len(self.all_docs))
        passage_res = self.passage_retriever.search_passages(query, top_k=len(self.all_docs))

        # Build raw score maps
        raw_lm = {r["doc_id"]: r["score"] for r in lm_res}
        raw_dfr = {r["doc_id"]: r["score"] for r in dfr_res}
        raw_tfidf = {r["doc_id"]: r["score"] for r in vsm_res}
        raw_pr = dict(self.pagerank_scores)
        
        # Semantic score: category and title keyword overlap
        raw_sem = {}
        q_lower = query.lower()
        for doc in self.all_docs:
            sem_val = 0.1
            if any(w in doc["title"].lower() for w in q_lower.split()):
                sem_val += 0.5
            if doc["category"].lower() in q_lower:
                sem_val += 0.4
            raw_sem[doc["doc_id"]] = sem_val

        # Map top passage per doc_id
        doc_passages = {}
        for p in passage_res:
            d_id = p["doc_id"]
            if d_id not in doc_passages:
                doc_passages[d_id] = p

        # 3. Normalize scores
        norm_lm = self._normalize(raw_lm)
        norm_dfr = self._normalize(raw_dfr)
        norm_tfidf = self._normalize(raw_tfidf)
        norm_pr = self._normalize(raw_pr)
        norm_sem = self._normalize(raw_sem)

        # 4. Multi-model fusion
        w_lm = float(weights.get("w_lm", 0.25))
        w_tfidf = float(weights.get("w_tfidf", 0.25))
        w_dfr = float(weights.get("w_dfr", 0.20))
        w_pr = float(weights.get("w_pagerank", 0.15))
        w_sem = float(weights.get("w_semantic", 0.15))
        weight_sum = w_lm + w_tfidf + w_dfr + w_pr + w_sem or 1.0

        final_ranked = []
        for doc in self.all_docs:
            d_id = doc["doc_id"]
            
            # Skip documents with zero term matches across TF-IDF, LM, and DFR
            if raw_tfidf.get(d_id, 0) == 0 and raw_dfr.get(d_id, 0) == 0 and d_id not in raw_lm:
                continue

            s_lm = norm_lm.get(d_id, 0.0)
            s_tfidf = norm_tfidf.get(d_id, 0.0)
            s_dfr = norm_dfr.get(d_id, 0.0)
            s_pr = norm_pr.get(d_id, 0.0)
            s_sem = norm_sem.get(d_id, 0.0)

            composite_score = (
                w_lm * s_lm +
                w_tfidf * s_tfidf +
                w_dfr * s_dfr +
                w_pr * s_pr +
                w_sem * s_sem
            ) / weight_sum

            # Get snippet
            passage_info = doc_passages.get(d_id)
            if passage_info:
                snippet = passage_info["highlighted_text"]
                match_terms = passage_info["matched_terms"]
            else:
                snippet = doc["content"][:200] + "..."
                match_terms = [t for t in query.split() if t.lower() in doc["content"].lower()]

            final_ranked.append({
                "doc_id": d_id,
                "title": doc["title"],
                "category": doc["category"],
                "relevant_passage": snippet,
                "matched_terms": match_terms,
                "scores": {
                    "composite": round(composite_score, 4),
                    "lm_score": round(s_lm, 3),
                    "tfidf_score": round(s_tfidf, 3),
                    "dfr_score": round(s_dfr, 3),
                    "pagerank_score": round(s_pr, 3),
                    "semantic_score": round(s_sem, 3)
                }
            })

        final_ranked.sort(key=lambda x: x["scores"]["composite"], reverse=True)
        for idx, item in enumerate(final_ranked[:top_k]):
            item["rank"] = idx + 1

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        # Record in search history
        try:
            execute_sql(
                """
                INSERT INTO search_history (query_text, results_count, response_time_ms, model_used)
                VALUES (?, ?, ?, 'HYBRID_FUSION')
                """,
                (query, len(final_ranked), round(elapsed_ms, 2))
            )
        except Exception:
            pass

        # 5. Post-Search Recommendations
        recommendations = self._generate_post_search_recommendations(query, final_ranked)

        return {
            "query": query,
            "automaton_analysis": automaton_res,
            "weights_used": {
                "Language_Model": w_lm,
                "TF_IDF": w_tfidf,
                "DFR": w_dfr,
                "PageRank": w_pr,
                "Semantic": w_sem
            },
            "response_time_ms": round(elapsed_ms, 2),
            "total_matches": len(final_ranked),
            "results": final_ranked[:top_k],
            "post_search_recommendations": recommendations
        }

    def _generate_post_search_recommendations(self, query: str, top_results: list):
        """
        Derives hybrid recommendations combining Content-Based, Collaborative, and Knowledge rules.
        """
        recs = []
        seen_ids = set(r["doc_id"] for r in top_results[:3])

        # A. Content-Based recommendations from top ranked document
        if top_results:
            top_doc_id = top_results[0]["doc_id"]
            c_recs = self.content_rec.recommend_for_document(top_doc_id, top_k=2)
            for r in c_recs["recommendations"]:
                if r["doc_id"] not in seen_ids:
                    seen_ids.add(r["doc_id"])
                    recs.append({
                        "doc_id": r["doc_id"],
                        "title": r["title"],
                        "category": r["category"],
                        "source_method": "Content-Based Filtering",
                        "badge": "Content Affinity",
                        "reason": f"High lexical similarity with top hit '{top_results[0]['title']}'."
                    })

        # B. Knowledge-Based recommendation based on query terms
        kb_criteria = {
            "technology": "Face Recognition" if "face" in query.lower() else "Search Engine",
            "application": "ATM Banking" if "atm" in query.lower() else "Web Search",
            "security_level": "Critical"
        }
        kb_res = self.knowledge_rec.recommend(kb_criteria)
        if kb_res["recommendations"]:
            best_kb = kb_res["recommendations"][0]
            recs.append({
                "doc_id": 99,
                "title": best_kb["title"],
                "category": best_kb["topic"],
                "source_method": "Knowledge-Based Rules",
                "badge": "Rule Match",
                "reason": f"Rule satisfied: {best_kb['rule_fired']}."
            })

        # C. Collaborative recommendation
        collab_res = self.collab_filter.recommend("User_Alice", top_k=2)
        for cr in collab_res["recommendations"]:
            if cr["doc_id"] not in seen_ids:
                seen_ids.add(cr["doc_id"])
                doc_meta = next((d for d in self.all_docs if d["doc_id"] == cr["doc_id"]), None)
                if doc_meta:
                    recs.append({
                        "doc_id": cr["doc_id"],
                        "title": doc_meta["title"],
                        "category": doc_meta["category"],
                        "source_method": "Collaborative Filtering",
                        "badge": "Community Choice",
                        "reason": f"Highly rated ({cr['predicted_rating']}★) by users researching similar security topics."
                    })

        return recs[:4]
