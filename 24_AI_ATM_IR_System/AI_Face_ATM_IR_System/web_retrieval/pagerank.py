from collections import defaultdict
from web_retrieval.link_rank import DEFAULT_WEB_GRAPH

class PageRankEngine:
    """
    PageRank Algorithm from Scratch.
    Computes stationary distribution vector p of a random surfer over directed web graph.
    
    Formula:
        PR(p_i) = (1 - d) / N + d * sum_{p_j in In(p_i)} ( PR(p_j) / Out(p_j) )
    
    Properties:
        - d: damping factor (typically 0.85)
        - Handling dangling nodes (out-degree = 0): distributed equally across all N pages
        - Iterative power method until sum(|PR_new - PR_old|) < epsilon
    """

    def __init__(self, edges=None, damping_factor: float = 0.85, epsilon: float = 1e-6, max_iter: int = 100):
        self.edges = edges or DEFAULT_WEB_GRAPH
        self.d = damping_factor
        self.epsilon = epsilon
        self.max_iter = max_iter

        # Build adjacency structures
        self.nodes = set()
        self.in_links = defaultdict(set)
        self.out_links = defaultdict(set)

        for u, v in self.edges:
            self.nodes.add(u)
            self.nodes.add(v)
            self.out_links[u].add(v)
            self.in_links[v].add(u)

        self.node_list = sorted(list(self.nodes))
        self.N = len(self.node_list)

    def compute(self):
        if self.N == 0:
            return {"results": [], "iterations": 0, "converged": True}

        # Initialize uniform distribution: 1 / N
        pr = {node: 1.0 / self.N for node in self.node_list}
        history = []

        iteration = 0
        converged = False

        while iteration < self.max_iter:
            iteration += 1
            new_pr = {}
            
            # Sum of PageRank for dangling nodes (out-degree == 0)
            dangling_sum = sum(pr[node] for node in self.node_list if len(self.out_links[node]) == 0)
            dangling_allocation = self.d * (dangling_sum / self.N)

            for i in self.node_list:
                # In-link summation
                incoming_sum = 0.0
                for j in self.in_links[i]:
                    out_deg = len(self.out_links[j])
                    if out_deg > 0:
                        incoming_sum += pr[j] / out_deg

                # PageRank transition formula
                new_pr[i] = ((1.0 - self.d) / self.N) + (self.d * incoming_sum) + dangling_allocation

            # Check convergence L1 norm
            diff = sum(abs(new_pr[n] - pr[n]) for n in self.node_list)
            history.append({
                "iteration": iteration,
                "residual_error": round(diff, 8)
            })

            pr = new_pr
            if diff < self.epsilon:
                converged = True
                break

        # Normalize so sum(PR) = 1.0
        total_sum = sum(pr.values())
        if total_sum > 0:
            pr = {n: v / total_sum for n, v in pr.items()}

        # Format sorted results
        ranked_pages = sorted(pr.items(), key=lambda x: x[1], reverse=True)
        results = []
        for idx, (page, score) in enumerate(ranked_pages):
            results.append({
                "rank": idx + 1,
                "page": page,
                "pagerank_score": round(score, 6),
                "percentage": f"{score * 100:.2f}%",
                "in_links_count": len(self.in_links[page]),
                "out_links_count": len(self.out_links[page])
            })

        # Vis.js network data with node size proportional to PageRank
        vis_nodes = []
        for r in results:
            vis_nodes.append({
                "id": r["page"],
                "label": r["page"].replace("_", " "),
                "value": int(r["pagerank_score"] * 200) + 12,
                "title": f"Rank #{r['rank']}<br>PageRank: {r['pagerank_score']}<br>Share: {r['percentage']}"
            })

        vis_edges = [
            {"from": u, "to": v, "arrows": "to"}
            for u, v in self.edges
        ]

        return {
            "damping_factor": self.d,
            "convergence_threshold": self.epsilon,
            "iterations_to_converge": iteration,
            "converged": converged,
            "final_residual": history[-1]["residual_error"] if history else 0.0,
            "results": results,
            "history": history[-5:],  # Last 5 convergence steps
            "vis_graph": {
                "nodes": vis_nodes,
                "edges": vis_edges
            }
        }
