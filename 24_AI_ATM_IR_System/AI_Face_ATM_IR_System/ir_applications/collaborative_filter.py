import math
from collections import defaultdict
from database.db import query_all

DEFAULT_INTERACTIONS = [
    # (user_id, product_id, rating)
    ("alex", 1, 5.0), ("alex", 2, 4.5), ("alex", 3, 5.0), ("alex", 4, 2.0),
    ("elena", 1, 4.0), ("elena", 2, 5.0), ("elena", 3, 4.0), ("elena", 4, 2.0),
    ("suyash_karandikar", 1, 5.0), ("suyash_karandikar", 3, 5.0), ("suyash_karandikar", 5, 4.5),
    ("admin", 2, 5.0), ("admin", 4, 5.0), ("admin", 5, 4.0),
    ("User_Alice", 1, 5.0), ("User_Alice", 2, 4.0), ("User_Alice", 3, 5.0), ("User_Alice", 4, 2.0),
    ("User_Bob", 1, 4.0),   ("User_Bob", 2, 5.0),   ("User_Bob", 3, 4.0),   ("User_Bob", 4, 2.0),
    ("User_Charlie", 1, 1.0), ("User_Charlie", 2, 2.0), ("User_Charlie", 3, 1.0), ("User_Charlie", 4, 5.0),
    ("User_David", 2, 4.0),   ("User_David", 3, 5.0),   ("User_David", 5, 4.0), ("User_David", 6, 2.0),
    ("User_Eva", 1, 5.0),     ("User_Eva", 4, 2.0),     ("User_Eva", 5, 5.0),   ("User_Eva", 6, 4.0),
]

PRODUCT_NAMES = {
    1: "4.25% High-Yield Wealth Vault",
    2: "Biometric Smart Chip Debit Card",
    3: "Zero-Liability Fraud Protection Shield",
    4: "Automated 50/30/20 Wealth Builder Plan",
    5: "Global Travel Debit Card (0% Forex)",
    6: "Emergency Cash Reserve Facility",
    7: "Instant Cardless ATM Withdrawal Pass",
    8: "Commercial Business Overdraft Buffer",
    9: "Dispute & Skimming Restitution Guarantee",
    10: "Smart APY Dividend Optimizer"
}

class CollaborativeFilter:
    """
    User-Based Collaborative Filtering Recommender System.
    Uses Cosine Similarity over user rating vectors to predict preference for unseen documents.
    """

    def __init__(self):
        # Load from DB if present, else fallback
        try:
            db_ratings = query_all("SELECT u.username as user_id, ui.doc_id, ui.rating FROM user_interactions ui JOIN users u ON ui.user_id = u.id")
        except Exception:
            db_ratings = []
        data = db_ratings if len(db_ratings) > 5 else DEFAULT_INTERACTIONS

        self.user_ratings = defaultdict(dict)
        self.item_ratings = defaultdict(dict)
        self.all_users = set()
        self.all_items = set()

        for entry in data:
            if isinstance(entry, dict):
                u, i, r = entry["user_id"], entry["doc_id"], float(entry["rating"])
            else:
                u, i, r = entry[0], entry[1], float(entry[2])
            self.user_ratings[u][i] = r
            self.item_ratings[i][u] = r
            self.all_users.add(u)
            self.all_items.add(i)

    def _cosine_sim(self, user1: str, user2: str) -> float:
        r1 = self.user_ratings.get(user1, {})
        r2 = self.user_ratings.get(user2, {})
        common_items = set(r1.keys()).intersection(set(r2.keys()))
        if not common_items:
            return 0.0

        dot = sum(r1[i] * r2[i] for i in common_items)
        norm1 = math.sqrt(sum(v * v for v in r1.values()))
        norm2 = math.sqrt(sum(v * v for v in r2.values()))
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def get_matrix_view(self):
        """
        Returns full user-item rating grid for UI rendering.
        """
        users = sorted(list(self.all_users))
        items = sorted(list(self.all_items))
        rows = []
        for u in users:
            row_dict = {"user": u, "ratings": {}}
            for i in items:
                row_dict["ratings"][str(i)] = self.user_ratings[u].get(i, "-")
            rows.append(row_dict)
        return {
            "users": users,
            "items": [str(i) for i in items],
            "matrix": rows
        }

    def recommend(self, target_user: str, top_k: int = 5):
        if target_user not in self.user_ratings:
            # Fallback for new user: recommend highest average rated items
            avg_ratings = []
            for item, raters in self.item_ratings.items():
                avg = sum(raters.values()) / len(raters)
                title = PRODUCT_NAMES.get(item, f"Banking Plan #{item}")
                avg_ratings.append({
                    "doc_id": item,
                    "title": title,
                    "product_name": title,
                    "predicted_rating": round(avg, 2),
                    "confidence": 0.5
                })
            avg_ratings.sort(key=lambda x: x["predicted_rating"], reverse=True)
            return {
                "target_user": target_user,
                "strategy": "Cold-Start Global Popularity",
                "similar_users": [],
                "recommendations": avg_ratings[:top_k]
            }

        # Calculate similarities to all other users
        sim_scores = {}
        for other in self.all_users:
            if other != target_user:
                sim = self._cosine_sim(target_user, other)
                if sim > 0:
                    sim_scores[other] = sim

        # Predict ratings for unrated items
        target_seen = set(self.user_ratings[target_user].keys())
        candidate_items = self.all_items - target_seen
        predictions = []

        for item in candidate_items:
            num = 0.0
            den = 0.0
            contributing_neighbors = 0

            for other, sim in sim_scores.items():
                if item in self.user_ratings[other]:
                    num += sim * self.user_ratings[other][item]
                    den += abs(sim)
                    contributing_neighbors += 1

            if den > 0:
                pred = num / den
                title = PRODUCT_NAMES.get(item, f"Banking Plan #{item}")
                predictions.append({
                    "doc_id": item,
                    "title": title,
                    "product_name": title,
                    "predicted_rating": round(pred, 2),
                    "confidence": round(min(1.0, den), 2),
                    "neighbors_used": contributing_neighbors,
                    "reason": f"Recommended with {pred:.1f}★ predicted satisfaction based on {contributing_neighbors} customer peers with similar financial patterns."
                })

        predictions.sort(key=lambda x: x["predicted_rating"], reverse=True)
        similar_users_list = [
            {"user": u, "similarity": round(s, 3)}
            for u, s in sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        return {
            "target_user": target_user,
            "strategy": "User-Based Collaborative Filtering (Cosine)",
            "similar_users": similar_users_list,
            "recommendations": predictions[:top_k]
        }
