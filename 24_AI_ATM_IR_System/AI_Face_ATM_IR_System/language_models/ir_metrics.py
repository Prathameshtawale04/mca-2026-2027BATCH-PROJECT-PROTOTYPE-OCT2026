class IREvaluator:
    """
    Standard Information Retrieval Evaluation Metrics:
    - Precision = |Retrieved & Relevant| / |Retrieved|
    - Recall = |Retrieved & Relevant| / |Relevant|
    - F1-Score = 2 * (P * R) / (P + R)
    - Precision@K = Precision evaluated at cutoff K
    - Average Precision (AP) = sum(P@k * rel(k)) / |Relevant|
    - Mean Average Precision (MAP) across benchmark query sets
    """

    @staticmethod
    def precision(retrieved: list, relevant: set) -> float:
        if not retrieved:
            return 0.0
        rel_retrieved = sum(1 for doc_id in retrieved if doc_id in relevant)
        return rel_retrieved / len(retrieved)

    @staticmethod
    def recall(retrieved: list, relevant: set) -> float:
        if not relevant:
            return 0.0
        rel_retrieved = sum(1 for doc_id in retrieved if doc_id in relevant)
        return rel_retrieved / len(relevant)

    @staticmethod
    def f1_score(precision_val: float, recall_val: float) -> float:
        if precision_val + recall_val == 0.0:
            return 0.0
        return 2.0 * (precision_val * recall_val) / (precision_val + recall_val)

    @staticmethod
    def precision_at_k(retrieved: list, relevant: set, k: int) -> float:
        if not retrieved or k <= 0:
            return 0.0
        sub_list = retrieved[:k]
        rel_retrieved = sum(1 for doc_id in sub_list if doc_id in relevant)
        return rel_retrieved / len(sub_list)

    @staticmethod
    def average_precision(retrieved: list, relevant: set) -> float:
        if not relevant:
            return 0.0
        running_sum = 0.0
        num_rel = 0
        for i, doc_id in enumerate(retrieved):
            if doc_id in relevant:
                num_rel += 1
                running_sum += (num_rel / (i + 1))
        return running_sum / len(relevant) if len(relevant) > 0 else 0.0

    @classmethod
    def evaluate_query(cls, retrieved_doc_ids: list, relevant_doc_ids: set):
        p = cls.precision(retrieved_doc_ids, relevant_doc_ids)
        r = cls.recall(retrieved_doc_ids, relevant_doc_ids)
        f1 = cls.f1_score(p, r)
        p3 = cls.precision_at_k(retrieved_doc_ids, relevant_doc_ids, 3)
        p5 = cls.precision_at_k(retrieved_doc_ids, relevant_doc_ids, 5)
        p10 = cls.precision_at_k(retrieved_doc_ids, relevant_doc_ids, 10)
        ap = cls.average_precision(retrieved_doc_ids, relevant_doc_ids)

        return {
            "retrieved_count": len(retrieved_doc_ids),
            "relevant_count": len(relevant_doc_ids),
            "precision": round(p, 4),
            "recall": round(r, 4),
            "f1_score": round(f1, 4),
            "p_at_3": round(p3, 4),
            "p_at_5": round(p5, 4),
            "p_at_10": round(p10, 4),
            "average_precision": round(ap, 4)
        }

    @classmethod
    def evaluate_benchmark(cls, query_eval_pairs: list):
        """
        Computes Mean Average Precision (MAP) across multiple queries:
        query_eval_pairs: list of (retrieved_ids, relevant_set)
        """
        if not query_eval_pairs:
            return {"map": 0.0, "queries_evaluated": 0, "details": []}

        aps = []
        details = []
        for idx, (retrieved, relevant) in enumerate(query_eval_pairs):
            metrics = cls.evaluate_query(retrieved, relevant)
            aps.append(metrics["average_precision"])
            details.append({
                "query_index": idx + 1,
                **metrics
            })

        mean_ap = sum(aps) / len(aps)
        return {
            "map": round(mean_ap, 4),
            "queries_evaluated": len(query_eval_pairs),
            "details": details
        }
