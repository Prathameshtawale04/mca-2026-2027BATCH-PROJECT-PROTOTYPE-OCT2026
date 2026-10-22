from database.db import query_all

KNOWLEDGE_CATALOG = [
    {
        "id": "KB01",
        "title": "Biometric ATM Security Architecture",
        "technology": "Face Recognition",
        "application": "ATM Banking",
        "security_level": "Critical",
        "difficulty": "Intermediate",
        "topic": "Biometrics",
        "description": "Comprehensive design for incorporating OpenCV LBPH and Haar cascade biometrics in ATM cash dispensing terminals."
    },
    {
        "id": "KB02",
        "title": "PBKDF2 & SHA-256 PIN Protection Protocol",
        "technology": "Cryptography",
        "application": "ATM Banking",
        "security_level": "Critical",
        "difficulty": "Advanced",
        "topic": "Cybersecurity",
        "description": "Salted key derivation functions and brute-force mitigation strategies for banking credentials."
    },
    {
        "id": "KB03",
        "title": "Distributed Inverted Indexing & Search Engine Design",
        "technology": "Search Engine",
        "application": "Web Search",
        "security_level": "Medium",
        "difficulty": "Advanced",
        "topic": "Information Retrieval",
        "description": "Multi-node sharded inverted indexing, term dictionaries, and MapReduce posting lists."
    },
    {
        "id": "KB04",
        "title": "PageRank Link Graph Analysis in Financial Intranets",
        "technology": "Machine Learning",
        "application": "Cybersecurity",
        "security_level": "High",
        "difficulty": "Intermediate",
        "topic": "Link Analysis",
        "description": "Eigenvector centrality and random walk models for structural fraud detection in transaction graphs."
    },
    {
        "id": "KB05",
        "title": "Multi-Factor Authentication & Account Lockout Standards",
        "technology": "Face Recognition",
        "application": "Multi-Factor Auth",
        "security_level": "Critical",
        "difficulty": "Beginner",
        "topic": "Biometrics",
        "description": "Compliance rules for 3-attempt account lockouts, biometric confidence thresholds, and audit logging."
    },
    {
        "id": "KB06",
        "title": "Semantic Web Knowledge Graphs for Banking Security",
        "technology": "Machine Learning",
        "application": "ATM Banking",
        "security_level": "High",
        "difficulty": "Intermediate",
        "topic": "Knowledge Representation",
        "description": "Subject-Predicate-Object triples ontology linking ATM components to security threat models."
    }
]

class KnowledgeBasedRecommender:
    """
    Knowledge-Based Recommendation Engine.
    Employs explicit domain inference rules and constraint satisfaction matching against
    structured knowledge catalog requirements.
    """

    def __init__(self, catalog=None):
        self.catalog = catalog or KNOWLEDGE_CATALOG

    def recommend(self, criteria: dict):
        """
        criteria: dict with keys:
            technology (str)
            application (str)
            security_level (str)
            difficulty (str)
        """
        user_tech = criteria.get("technology", "").strip().lower()
        user_app = criteria.get("application", "").strip().lower()
        user_sec = criteria.get("security_level", "").strip().lower()
        user_diff = criteria.get("difficulty", "").strip().lower()

        scored_items = []

        for item in self.catalog:
            match_points = 0
            max_points = 0
            satisfied_rules = []

            # 1. Technology constraint
            if user_tech:
                max_points += 30
                if user_tech in item["technology"].lower():
                    match_points += 30
                    satisfied_rules.append(f"Technology matches requested '{item['technology']}'")

            # 2. Application constraint
            if user_app:
                max_points += 30
                if user_app in item["application"].lower():
                    match_points += 30
                    satisfied_rules.append(f"Domain matches requested '{item['application']}'")

            # 3. Security Level constraint
            if user_sec:
                max_points += 20
                if user_sec in item["security_level"].lower():
                    match_points += 20
                    satisfied_rules.append(f"Meets security level criteria '{item['security_level']}'")

            # 4. Difficulty constraint
            if user_diff:
                max_points += 20
                if user_diff in item["difficulty"].lower():
                    match_points += 20
                    satisfied_rules.append(f"Difficulty aligns with '{item['difficulty']}'")

            if max_points == 0:
                match_pct = 100.0
            else:
                match_pct = round((match_points / max_points) * 100.0, 1)

            if match_pct > 0:
                scored_items.append({
                    "id": item["id"],
                    "title": item["title"],
                    "technology": item["technology"],
                    "application": item["application"],
                    "security_level": item["security_level"],
                    "difficulty": item["difficulty"],
                    "topic": item["topic"],
                    "description": item["description"],
                    "match_percentage": match_pct,
                    "satisfied_rules": satisfied_rules,
                    "rule_fired": " AND ".join(satisfied_rules) if satisfied_rules else "Default general match"
                })

        scored_items.sort(key=lambda x: x["match_percentage"], reverse=True)
        return {
            "criteria_applied": criteria,
            "total_matches": len(scored_items),
            "recommendations": scored_items
        }
