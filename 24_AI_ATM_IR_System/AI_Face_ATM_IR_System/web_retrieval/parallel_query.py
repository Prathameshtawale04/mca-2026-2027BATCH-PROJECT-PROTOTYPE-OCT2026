import time
import concurrent.futures
from database.db import query_all
from language_models.lm_ranker import LanguageModelRanker

class ParallelQueryCoordinator:
    """
    Parallel Information Retrieval Coordinator.
    Distributes user queries across multiple virtual nodes/shards concurrently using
    concurrent.futures, measures per-node execution latency, and aggregates ranked results.
    """

    def __init__(self, num_nodes: int = 3):
        self.num_nodes = num_nodes
        self.all_docs = query_all("SELECT doc_id, title, category, content FROM documents")
        self.shards = self._partition_documents()

    def _partition_documents(self):
        shards = [[] for _ in range(self.num_nodes)]
        for idx, doc in enumerate(self.all_docs):
            shards[idx % self.num_nodes].append(doc)
        return shards

    def _node_search(self, node_id: int, shard_docs: list, query: str):
        start_time = time.perf_counter()
        
        # Local language model ranker on shard documents
        ranker = LanguageModelRanker(documents=shard_docs)
        results = ranker.rank(query)
        
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "node_id": f"Node-{node_id + 1}",
            "docs_in_shard": len(shard_docs),
            "latency_ms": round(elapsed_ms, 2),
            "results": results[:5]  # Top 5 from this node
        }

    def execute_parallel_search(self, query: str):
        overall_start = time.perf_counter()
        node_reports = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_nodes) as executor:
            futures = {
                executor.submit(self._node_search, i, self.shards[i], query): i
                for i in range(self.num_nodes)
            }
            for future in concurrent.futures.as_completed(futures):
                node_reports.append(future.result())

        node_reports.sort(key=lambda x: x["node_id"])
        
        # Aggregate and merge results
        aggregated = []
        for report in node_reports:
            aggregated.extend(report["results"])

        # Sort aggregated results descending by score
        aggregated.sort(key=lambda x: x["score"], reverse=True)
        for idx, item in enumerate(aggregated):
            item["final_rank"] = idx + 1

        total_elapsed_ms = (time.perf_counter() - overall_start) * 1000.0

        return {
            "query": query,
            "node_count": self.num_nodes,
            "total_documents": len(self.all_docs),
            "total_latency_ms": round(total_elapsed_ms, 2),
            "node_reports": node_reports,
            "final_results": aggregated[:10]
        }
