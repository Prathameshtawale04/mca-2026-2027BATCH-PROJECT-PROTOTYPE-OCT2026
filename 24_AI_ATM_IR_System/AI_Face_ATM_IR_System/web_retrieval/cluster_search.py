import re
from collections import Counter
from database.db import query_all
from web_retrieval.search_engine import MiniSearchEngine

class ClusterSearchEngine:
    """
    Cluster-Based Search Engine Architecture.
    Organizes document collections into thematic clusters:
    - Cluster 1: Security & Biometric Authentication
    - Cluster 2: Banking & ATM Financial Systems
    - Cluster 3: Search Technology & IR Algorithms
    
    A query coordinator matches the query to cluster profiles, routes the query to
    relevant cluster nodes, and aggregates the cluster search results.
    """

    def __init__(self):
        all_docs = query_all("SELECT doc_id, title, category, content FROM documents")
        self.clusters = {
            "Security_Biometrics": {
                "name": "Security & Biometric Cluster",
                "keywords": ["face", "recognition", "biometric", "security", "authentication", "lbph", "camera", "pin", "lockout"],
                "docs": []
            },
            "Banking_Financial": {
                "name": "Banking & ATM Systems Cluster",
                "keywords": ["atm", "banking", "deposit", "withdrawal", "transaction", "balance", "account", "ledger", "card"],
                "docs": []
            },
            "IR_Technology": {
                "name": "IR & Search Engine Cluster",
                "keywords": ["retrieval", "search", "pagerank", "crawling", "inverted", "index", "vector", "tfidf", "language", "model"],
                "docs": []
            }
        }
        self._assign_documents_to_clusters(all_docs)

    def _tokenize(self, text: str):
        return set(re.findall(r'[a-zA-Z0-9]+', text.lower()))

    def _assign_documents_to_clusters(self, docs):
        for doc in docs:
            tokens = self._tokenize(f"{doc['title']} {doc['category']} {doc['content']}")
            # Score each cluster affinity
            scores = {}
            for c_key, c_info in self.clusters.items():
                intersection = tokens.intersection(set(c_info["keywords"]))
                scores[c_key] = len(intersection)
            
            # Default to largest intersection or IR cluster
            best_cluster = max(scores, key=scores.get)
            self.clusters[best_cluster]["docs"].append(doc)

        # Build MiniSearchEngine for each cluster
        for c_key in self.clusters:
            self.clusters[c_key]["engine"] = MiniSearchEngine(self.clusters[c_key]["docs"])

    def route_and_search(self, query: str):
        q_tokens = self._tokenize(query)
        cluster_affinities = []

        # 1. Cluster Scoring
        for c_key, c_info in self.clusters.items():
            overlap = q_tokens.intersection(set(c_info["keywords"]))
            affinity = len(overlap) / max(1, len(q_tokens))
            cluster_affinities.append({
                "cluster_key": c_key,
                "cluster_name": c_info["name"],
                "doc_count": len(c_info["docs"]),
                "affinity_score": round(affinity, 3),
                "matched_keywords": list(overlap)
            })

        cluster_affinities.sort(key=lambda x: x["affinity_score"], reverse=True)

        # 2. Query execution across clusters
        cluster_results = {}
        merged_results = []
        for c_item in cluster_affinities:
            c_key = c_item["cluster_key"]
            engine = self.clusters[c_key]["engine"]
            results = engine.search(query, top_k=5)
            
            cluster_results[c_key] = {
                "cluster_name": self.clusters[c_key]["name"],
                "affinity": c_item["affinity_score"],
                "results": results
            }
            for r in results:
                r_copy = dict(r)
                # Boost score by cluster affinity
                r_copy["cluster_source"] = self.clusters[c_key]["name"]
                r_copy["routed_score"] = round(r["score"] * (1.0 + c_item["affinity_score"]), 4)
                merged_results.append(r_copy)

        merged_results.sort(key=lambda x: x["routed_score"], reverse=True)
        for idx, item in enumerate(merged_results):
            item["global_rank"] = idx + 1

        return {
            "query": query,
            "cluster_routing": cluster_affinities,
            "cluster_breakdown": cluster_results,
            "final_ranked_results": merged_results[:10]
        }
