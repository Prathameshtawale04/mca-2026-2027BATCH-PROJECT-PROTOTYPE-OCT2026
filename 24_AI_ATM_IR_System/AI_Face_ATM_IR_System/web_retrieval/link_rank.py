import networkx as nx
from database.db import query_all

DEFAULT_WEB_GRAPH = [
    ("Page_A_ATM_Portal", "Page_B_Face_Verification"),
    ("Page_A_ATM_Portal", "Page_C_Security_Protocols"),
    ("Page_B_Face_Verification", "Page_C_Security_Protocols"),
    ("Page_C_Security_Protocols", "Page_A_ATM_Portal"),
    ("Page_D_Information_Retrieval", "Page_E_Search_Engine"),
    ("Page_E_Search_Engine", "Page_F_PageRank_Algorithm"),
    ("Page_F_PageRank_Algorithm", "Page_A_ATM_Portal"),
    ("Page_B_Face_Verification", "Page_F_PageRank_Algorithm"),
    ("Page_G_Recommender_Systems", "Page_D_Information_Retrieval"),
    ("Page_G_Recommender_Systems", "Page_C_Security_Protocols")
]

class LinkRankAnalyzer:
    """
    Link-Based Web Ranking using NetworkX.
    Computes graph topological metrics: In-Degree, Out-Degree, Authority, and Hub scores.
    Outputs interactive graph nodes and edges for Vis.js.
    """

    def __init__(self, edges=None):
        self.edges = edges or DEFAULT_WEB_GRAPH
        self.G = nx.DiGraph()
        for u, v in self.edges:
            self.G.add_edge(u, v)

    def analyze(self):
        nodes = list(self.G.nodes())
        in_degrees = dict(self.G.in_degree())
        out_degrees = dict(self.G.out_degree())
        
        # HITS algorithm (Hubs and Authorities)
        try:
            hubs, authorities = nx.hits(self.G, max_iter=100, normalized=True)
        except Exception:
            hubs = {n: 1.0 / len(nodes) for n in nodes}
            authorities = {n: 1.0 / len(nodes) for n in nodes}

        # Betweenness centrality
        betweenness = nx.betweenness_centrality(self.G)

        summary_table = []
        for n in nodes:
            summary_table.append({
                "page": n,
                "in_degree": in_degrees.get(n, 0),
                "out_degree": out_degrees.get(n, 0),
                "authority_score": round(authorities.get(n, 0.0), 4),
                "hub_score": round(hubs.get(n, 0.0), 4),
                "betweenness": round(betweenness.get(n, 0.0), 4)
            })

        # Rank by in-degree / authority
        summary_table.sort(key=lambda x: x["authority_score"], reverse=True)
        for idx, item in enumerate(summary_table):
            item["rank"] = idx + 1

        # Format for Vis.js network
        vis_nodes = []
        for row in summary_table:
            vis_nodes.append({
                "id": row["page"],
                "label": row["page"].replace("_", " "),
                "value": row["in_degree"] * 5 + 10,  # node size proportional to in-degree
                "title": f"In-Degree: {row['in_degree']}<br>Authority: {row['authority_score']}<br>Hub: {row['hub_score']}"
            })

        vis_edges = [
            {"from": u, "to": v, "arrows": "to"}
            for u, v in self.edges
        ]

        return {
            "node_count": len(nodes),
            "edge_count": len(self.edges),
            "summary_table": summary_table,
            "vis_graph": {
                "nodes": vis_nodes,
                "edges": vis_edges
            }
        }
