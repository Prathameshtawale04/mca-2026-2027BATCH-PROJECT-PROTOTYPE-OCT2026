import json
import networkx as nx
from database.db import query_all, execute_sql

DEFAULT_TRIPLES = [
    {"subject": "ATM System", "predicate": "uses", "object": "Face Recognition"},
    {"subject": "Face Recognition", "predicate": "extracts", "object": "LBPH Biometric Features"},
    {"subject": "Face Recognition", "predicate": "provides", "object": "Biometric Authentication"},
    {"subject": "Biometric Authentication", "predicate": "protects", "object": "Customer Bank Account"},
    {"subject": "Customer Bank Account", "predicate": "enforces", "object": "Daily Withdrawal Limit"},
    {"subject": "ATM System", "predicate": "verifies", "object": "PBKDF2 Hashed PIN"},
    {"subject": "Anti-Spoofing Engine", "predicate": "measures", "object": "Laplacian Variance Liveness"},
    {"subject": "ATM Terminal", "predicate": "reportsIncidentsTo", "object": "Security Operations Center"},
    {"subject": "Security Operations Center", "predicate": "monitors", "object": "Fraudulent Cash Withdrawals"},
    {"subject": "High-Yield Vault", "predicate": "earnsCompoundInterest", "object": "Savings Account"},
    {"subject": "Smart Biometric Card", "predicate": "requires", "object": "Two-Factor Authentication"},
    {"subject": "Search Engine", "predicate": "indexes", "object": "Inverted Index"},
    {"subject": "Inverted Index", "predicate": "accelerates", "object": "Query Processing"},
    {"subject": "PageRank", "predicate": "analyzes", "object": "Hyperlink Graph"},
    {"subject": "PageRank", "predicate": "calculates", "object": "Document Authority"},
    {"subject": "Information Retrieval", "predicate": "ranksWith", "object": "Language Model Query Likelihood"},
    {"subject": "Collaborative Filtering", "predicate": "recommends", "object": "Banking Wealth Products"},
    {"subject": "Knowledge Graph", "predicate": "represents", "object": "Semantic Triples"}
]

class SemanticKnowledgeGraph:
    """
    Semantic Web RDF-style Knowledge Graph.
    Models Subject-Predicate-Object triples as a directed multigraph using NetworkX.
    Exports to Vis.js network visualization format with edge relationship labels.
    """

    def __init__(self):
        self.G = nx.DiGraph()
        self.triples = []
        self._load_triples()

    def _load_triples(self):
        db_triples = query_all("SELECT subject, predicate, object, confidence FROM knowledge_triples")
        if len(db_triples) > 5:
            self.triples = [dict(t) for t in db_triples]
        else:
            self.triples = list(DEFAULT_TRIPLES)

        for t in self.triples:
            s, p, o = t["subject"], t["predicate"], t["object"]
            self.G.add_node(s)
            self.G.add_node(o)
            self.G.add_edge(s, o, relation=p)

    def add_triple(self, subject: str, predicate: str, object_entity: str, confidence: float = 1.0):
        t = {
            "subject": subject.strip(),
            "predicate": predicate.strip(),
            "object": object_entity.strip(),
            "confidence": confidence
        }
        self.triples.append(t)
        self.G.add_node(t["subject"])
        self.G.add_node(t["object"])
        self.G.add_edge(t["subject"], t["object"], relation=t["predicate"])

        execute_sql(
            """
            INSERT INTO knowledge_triples (subject, predicate, object, confidence)
            VALUES (?, ?, ?, ?)
            """,
            (t["subject"], t["predicate"], t["object"], confidence)
        )
        return True

    def query_subgraph(self, entity_keyword: str = None):
        """
        Returns nodes and edges formatted for Vis.js interactive graph rendering.
        """
        nodes = list(self.G.nodes())
        filtered_nodes = set()

        if entity_keyword:
            kw = entity_keyword.lower()
            for n in nodes:
                if kw in n.lower():
                    filtered_nodes.add(n)
                    # Add 1-hop neighbors
                    filtered_nodes.update(self.G.successors(n))
                    filtered_nodes.update(self.G.predecessors(n))
        else:
            filtered_nodes = set(nodes)

        # Build Vis.js nodes
        vis_nodes = []
        for n in filtered_nodes:
            in_deg = self.G.in_degree(n)
            out_deg = self.G.out_degree(n)
            # Distinct styling for ATM/Security vs IR concepts
            is_atm = any(k in n.lower() for k in ["atm", "face", "security", "pin", "biometric", "withdrawal", "account", "bank", "vault", "card", "spoofing", "center", "liveness", "limit"])
            group = "atm_security" if is_atm else "information_retrieval"
            color = "#10b981" if is_atm else "#3b82f6"

            vis_nodes.append({
                "id": n,
                "label": n,
                "group": group,
                "color": {"background": color, "border": "#ffffff"},
                "font": {"color": "#ffffff", "face": "Inter, sans-serif"},
                "value": (in_deg + out_deg) * 6 + 14,
                "title": f"<b>{n}</b><br>Incoming links: {in_deg}<br>Outgoing links: {out_deg}"
            })

        # Build Vis.js edges
        vis_edges = []
        for u, v, data in self.G.edges(data=True):
            if u in filtered_nodes and v in filtered_nodes:
                vis_edges.append({
                    "from": u,
                    "to": v,
                    "label": data.get("relation", "relatesTo"),
                    "arrows": "to",
                    "font": {"size": 11, "align": "middle", "color": "#94a3b8"},
                    "color": {"color": "#64748b", "highlight": "#38bdf8"}
                })

        return {
            "entity_count": len(vis_nodes),
            "relationship_count": len(vis_edges),
            "triples": [
                t for t in self.triples
                if t["subject"] in filtered_nodes and t["object"] in filtered_nodes
            ],
            "vis_graph": {
                "nodes": vis_nodes,
                "edges": vis_edges
            }
        }
