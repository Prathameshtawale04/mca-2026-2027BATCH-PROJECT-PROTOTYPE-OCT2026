import math
import re
from collections import Counter, defaultdict

# Comprehensive banking knowledge base
BANKING_KNOWLEDGE_BASE = [
    {
        "id": "kb_01",
        "title": "ATM Daily Withdrawal Limits & Overdraft Rules",
        "category": "limits",
        "content": "Customers can withdraw up to $2,000 per rolling 24-hour window across all ATM terminals. Single transaction limit is $800. If an attempted withdrawal exceeds the available account balance or daily limit, the transaction is declined with no fee for active checking accounts.",
        "tags": ["daily limit", "withdrawal", "overdraft", "maximum cash", "atm limit"]
    },
    {
        "id": "kb_02",
        "title": "Face Biometric Recognition & Liveness Anti-Spoofing",
        "category": "security",
        "content": "Mira AI utilizes 128-dimensional biometric facial embedding vectors combined with multi-factor liveness testing. Anti-spoofing algorithms evaluate Laplacian micro-texture sharpness, screen specular reflection, and skin chrominance to prevent attacks from photos, videos, or masks.",
        "tags": ["face recognition", "biometrics", "liveness", "anti spoofing", "facial login"]
    },
    {
        "id": "kb_03",
        "title": "Instant Emergency Card & Account Freeze",
        "category": "security",
        "content": "If you suspect unauthorized activity or lose your ATM card, you can immediately freeze your account via the customer portal or by telling Mira AI 'freeze my card'. When frozen, all cash withdrawals, transfers, and point-of-sale operations are instantly halted until admin verification.",
        "tags": ["freeze card", "emergency freeze", "lost card", "stolen", "account security"]
    },
    {
        "id": "kb_04",
        "title": "Inter-Bank Funds Transfer Fees and Timelines",
        "category": "transfers",
        "content": "Internal transfers between Mira AI accounts are instantaneous with $0.00 zero fees. External wire transfers settle within 1 business day. A $1.50 network charge applies to non-network third-party transfers. Daily outgoing transfer ceiling is $5,000.",
        "tags": ["transfer", "fees", "wire transfer", "send money", "ach"]
    },
    {
        "id": "kb_05",
        "title": "Personalized 50/30/20 Smart Savings Advice",
        "category": "savings",
        "content": "Mira AI recommends the 50/30/20 financial rule: allocate 50% of monthly income to essentials, 30% to discretionary spending, and 20% to emergency savings and investments. Automated round-up features deposit spare change into linked savings goals on every debit transaction.",
        "tags": ["savings plan", "50 30 20 rule", "budgeting", "emergency fund", "auto save"]
    },
    {
        "id": "kb_06",
        "title": "ATM PIN Safety, Attempts Lockout & Reset",
        "category": "security",
        "content": "Three consecutive incorrect PIN entries will automatically lock your ATM card for 24 hours to prevent brute-force attacks. You can reset your PIN securely at any Mira ATM using two-factor biometric face verification and your registered mobile phone OTP.",
        "tags": ["pin reset", "locked pin", "failed attempts", "atm pin", "password"]
    },
    {
        "id": "kb_07",
        "title": "Fraud Detection, Velocity Rules and Dispute Resolution",
        "category": "fraud",
        "content": "Our machine learning engine flags unusual transaction velocities, abnormal midnight withdrawals, and geographical distance leaps. If a transaction is flagged, funds are temporarily held in escrow. To dispute an unauthorized charge, file an incident report within 60 days for 100% liability coverage.",
        "tags": ["fraud detection", "dispute", "unauthorized charge", "chargeback", "stolen funds"]
    },
    {
        "id": "kb_08",
        "title": "Cash Deposit Processing and Envelope-Free Validation",
        "category": "deposits",
        "content": "Mira ATMs feature intelligent optical note validators. Insert up to 50 bills simultaneously without envelopes. Notes are instantly verified for authenticity and credited to your checking or savings account balance in real-time.",
        "tags": ["cash deposit", "deposit cash", "note validator", "atm deposit"]
    },
    {
        "id": "kb_09",
        "title": "High-Yield Savings Accounts & Interest Accrual",
        "category": "products",
        "content": "Our High-Yield Savings Account provides a 4.25% Annual Percentage Yield (APY) compounded daily and credited on the first of each calendar month. There are no minimum balance requirements or maintenance fees.",
        "tags": ["high yield savings", "interest rate", "apy", "savings account", "investment"]
    },
    {
        "id": "kb_10",
        "title": "International ATM Usage & Foreign Exchange Margins",
        "category": "travel",
        "content": "Before traveling abroad, notify Mira AI or enable travel mode in your customer settings. International ATM cash withdrawals carry a flat 1.0% foreign exchange conversion margin and no international ATM surcharge at partner worldwide networks.",
        "tags": ["international travel", "foreign currency", "travel mode", "overseas atm"]
    }
]

# Security incident corpus for Admin SOC Log Search
SECURITY_INCIDENT_CORPUS = [
    {
        "id": "sec_01",
        "title": "Multiple Face Verification Mismatch Alert",
        "category": "biometric_anomaly",
        "content": "Repeated face recognition failures detected at ATM Terminal #04. Five consecutive attempts showed cosine similarity below 0.35 threshold. Anti-spoofing flags reported static printed portrait texture.",
        "tags": ["face mismatch", "spoofing attempt", "terminal 04", "biometric alert"]
    },
    {
        "id": "sec_02",
        "title": "Rapid Velocity Withdrawal Spree (Card Skimming Signature)",
        "category": "fraud_velocity",
        "content": "Four successive $500 maximum withdrawals requested within 180 seconds on account ACC-9821. Transaction velocity deviation exceeded 4.8 standard deviations. Machine learning model triggered immediate hold.",
        "tags": ["velocity spike", "card skimming", "abnormal withdrawal", "rapid cash"]
    },
    {
        "id": "sec_03",
        "title": "Midnight High-Value Drain Attempt Outside Behavioral Baseline",
        "category": "behavioral_fraud",
        "content": "Attempted withdrawal of $1,800 at 03:42 AM. Historical profile indicates customer exclusively conducts small daylight transactions (<$100). Isolation Forest flagged anomaly score 0.89.",
        "tags": ["midnight withdrawal", "anomaly score", "unusual hour", "high value drain"]
    },
    {
        "id": "sec_04",
        "title": "Screen Video Replay Spoofing Detected by Liveness Engine",
        "category": "liveness_breach",
        "content": "ATM optical sensor captured high-frequency moiré patterns and intense specular reflection indicative of an iPad or smartphone screen replay attack. Authentication terminated immediately.",
        "tags": ["moire pattern", "screen replay", "liveness failed", "specular glare"]
    },
    {
        "id": "sec_05",
        "title": "Brute-Force ATM PIN Attack Mitigation",
        "category": "credential_attack",
        "content": "User card 4029-XXXX-8821 locked following three consecutive wrong PIN attempts within 60 seconds. Terminal camera snapshot archived to incident forensics log.",
        "tags": ["brute force", "wrong pin", "card locked", "lockout"]
    },
    {
        "id": "sec_06",
        "title": "Geographical Impossible Travel Anomaly",
        "category": "geo_anomaly",
        "content": "Card used in Chicago terminal followed 12 minutes later by a transaction attempt at New York ATM. Calculated physical transit velocity is physically impossible (4,200 mph). Card frozen automatically.",
        "tags": ["impossible travel", "geographic anomaly", "cloned card", "fraud"]
    }
]

# Stopwords for English
STOPWORDS = set([
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", 
    "by", "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", 
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", 
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", 
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on", "once", 
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", 
    "she", "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "these", "they", "this", "those", "through", "to", "too", 
    "under", "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", 
    "while", "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
])


def tokenize(text: str) -> list[str]:
    """Tokenizes text, strips punctuation, normalizes case and removes stop words."""
    words = re.findall(r'\b[a-zA-Z0-9_\-]{2,}\b', text.lower())
    return [w for w in words if w not in STOPWORDS]


class InformationRetrievalEngine:
    """
    Complete Information Retrieval Engine providing:
    1. TF-IDF with Cosine Similarity
    2. BM25 (Best Matching 25)
    3. Query-Likelihood Language Model with Dirichlet Smoothing & Jelinek-Mercer
    """

    def __init__(self, corpus: list[dict]):
        self.corpus = corpus
        self.doc_tokens = {}
        self.doc_lengths = {}
        self.total_docs = len(corpus)
        self.doc_freqs = defaultdict(int)
        self.term_freqs = defaultdict(lambda: defaultdict(int))
        self.collection_freqs = defaultdict(int)
        self.total_collection_tokens = 0
        self.avg_doc_length = 0

        self._build_index()

    def _build_index(self):
        total_len = 0
        for doc in self.corpus:
            doc_id = doc["id"]
            # Combine title, content, and tags
            combined_text = f"{doc['title']} {doc['content']} {' '.join(doc.get('tags', []))}"
            tokens = tokenize(combined_text)
            self.doc_tokens[doc_id] = tokens
            doc_len = len(tokens)
            self.doc_lengths[doc_id] = doc_len
            total_len += doc_len

            seen_terms = set()
            for t in tokens:
                self.term_freqs[doc_id][t] += 1
                self.collection_freqs[t] += 1
                self.total_collection_tokens += 1
                if t not in seen_terms:
                    self.doc_freqs[t] += 1
                    seen_terms.add(t)

        self.avg_doc_length = total_len / max(1, self.total_docs)

    # ---------------- 1. TF-IDF Algorithm ----------------
    def search_tfidf(self, query: str, top_k: int = 5) -> list[dict]:
        """
        TF-IDF with sublinear term-frequency scaling and cosine normalization.
        TF = 1 + log(tf) if tf > 0 else 0
        IDF = log(1 + (N - df + 0.5) / (df + 0.5))
        """
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        q_tf = Counter(q_tokens)
        q_weights = {}
        q_norm_sq = 0.0

        for t, tf in q_tf.items():
            if t in self.doc_freqs:
                df = self.doc_freqs[t]
                idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
                weight = (1.0 + math.log(tf)) * idf
                q_weights[t] = weight
                q_norm_sq += weight ** 2

        q_norm = math.sqrt(q_norm_sq) if q_norm_sq > 0 else 1.0

        scores = {}
        for doc in self.corpus:
            doc_id = doc["id"]
            dot_product = 0.0
            doc_norm_sq = 0.0

            for t, tf in self.term_freqs[doc_id].items():
                df = self.doc_freqs[t]
                idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
                w_d = (1.0 + math.log(tf)) * idf
                doc_norm_sq += w_d ** 2

                if t in q_weights:
                    dot_product += q_weights[t] * w_d

            doc_norm = math.sqrt(doc_norm_sq) if doc_norm_sq > 0 else 1.0
            score = dot_product / (q_norm * doc_norm) if (q_norm * doc_norm) > 0 else 0.0
            if score > 0:
                scores[doc_id] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return self._format_results(ranked, algorithm="TF-IDF")

    # ---------------- 2. BM25 Algorithm ----------------
    def search_bm25(self, query: str, top_k: int = 5, k1: float = 1.5, b: float = 0.75) -> list[dict]:
        """
        Okapi BM25 Ranking Algorithm.
        Score(D, Q) = Sum [ IDF(q) * (f(q, D) * (k1 + 1)) / (f(q, D) + k1 * (1 - b + b * (|D| / avgdl))) ]
        """
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        scores = {}
        for doc in self.corpus:
            doc_id = doc["id"]
            d_len = self.doc_lengths[doc_id]
            doc_score = 0.0

            for q in q_tokens:
                if q in self.doc_freqs:
                    df = self.doc_freqs[q]
                    idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))
                    f_qd = self.term_freqs[doc_id].get(q, 0)
                    
                    if f_qd > 0:
                        denom = f_qd + k1 * (1.0 - b + b * (d_len / self.avg_doc_length))
                        numerator = f_qd * (k1 + 1.0)
                        doc_score += idf * (numerator / denom)

            if doc_score > 0:
                scores[doc_id] = doc_score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return self._format_results(ranked, algorithm="BM25")

    # ---------------- 3. Query-Likelihood Language Model ----------------
    def search_query_likelihood(
        self,
        query: str,
        top_k: int = 5,
        smoothing: str = "dirichlet",
        mu: float = 1000.0,
        lambda_param: float = 0.3
    ) -> list[dict]:
        """
        Probabilistic Query-Likelihood Language Model with:
        - Dirichlet Prior Smoothing: P(w|D) = (c(w, D) + mu * P(w|C)) / (|D| + mu)
        - Jelinek-Mercer Smoothing: P(w|D) = (1 - lambda) * (c(w, D) / |D|) + lambda * P(w|C)
        """
        q_tokens = tokenize(query)
        if not q_tokens:
            return []

        scores = {}
        for doc in self.corpus:
            doc_id = doc["id"]
            d_len = self.doc_lengths[doc_id]
            log_likelihood = 0.0
            matched_terms = 0

            for q in q_tokens:
                # Background collection probability P(w|C)
                cf = self.collection_freqs.get(q, 0)
                p_coll = (cf / self.total_collection_tokens) if self.total_collection_tokens > 0 else 1e-6
                if p_coll == 0:
                    p_coll = 1e-6

                c_wd = self.term_freqs[doc_id].get(q, 0)
                if c_wd > 0:
                    matched_terms += 1

                if smoothing == "dirichlet":
                    # Dirichlet smoothing
                    p_wd = (c_wd + mu * p_coll) / (d_len + mu)
                else:
                    # Jelinek-Mercer smoothing
                    p_wd = (1.0 - lambda_param) * (c_wd / max(1, d_len)) + lambda_param * p_coll

                log_likelihood += math.log(max(1e-10, p_wd))

            # Only return documents that had at least one matching term
            if matched_terms > 0:
                scores[doc_id] = log_likelihood

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return self._format_results(ranked, algorithm=f"Query-Likelihood ({smoothing.capitalize()})")

    def _format_results(self, ranked_pairs: list[tuple[str, float]], algorithm: str) -> list[dict]:
        doc_map = {d["id"]: d for d in self.corpus}
        results = []
        max_score = ranked_pairs[0][1] if ranked_pairs else 1.0

        for rank, (doc_id, score) in enumerate(ranked_pairs, start=1):
            doc = doc_map.get(doc_id)
            if not doc:
                continue

            # Normalize score for friendly UI presentation (0 - 100%)
            if "Query-Likelihood" in algorithm:
                # Log-likelihood is negative; normalize to relative percentage
                norm_score = max(5.0, min(99.0, 100.0 + (score * 4.5)))
            else:
                norm_score = round(min(100.0, (score / max(1e-5, max_score)) * 100.0), 1)

            results.append({
                "rank": rank,
                "doc_id": doc_id,
                "title": doc["title"],
                "category": doc.get("category", "General"),
                "content": doc["content"],
                "raw_score": round(score, 4),
                "relevance_score": norm_score,
                "algorithm": algorithm
            })
        return results

    def compare_all(self, query: str, top_k: int = 3) -> dict:
        """Runs query across all 3 IR algorithms simultaneously for comparison."""
        tfidf_res = self.search_tfidf(query, top_k=top_k)
        bm25_res = self.search_bm25(query, top_k=top_k)
        ql_res = self.search_query_likelihood(query, top_k=top_k, smoothing="dirichlet")

        return {
            "query": query,
            "tfidf": tfidf_res,
            "bm25": bm25_res,
            "query_likelihood": ql_res,
        }


# Evaluation benchmark suite
def evaluate_ir_algorithms(engine: InformationRetrievalEngine) -> dict:
    """
    Evaluates IR algorithms on benchmark test queries with ground-truth relevant doc IDs.
    Calculates Precision@K, Recall@K, MAP (Mean Average Precision), MRR (Mean Reciprocal Rank).
    """
    benchmark_queries = [
        {"query": "how much cash can i withdraw per day limit", "relevant": ["kb_01"]},
        {"query": "facial recognition and liveness camera security", "relevant": ["kb_02"]},
        {"query": "freeze card emergency lost or stolen", "relevant": ["kb_03"]},
        {"query": "money transfer wire fees and limits", "relevant": ["kb_04"]},
        {"query": "50 30 20 savings plan advice budget", "relevant": ["kb_05"]},
        {"query": "wrong pin code locked account reset", "relevant": ["kb_06"]},
        {"query": "unauthorized fraudulent transaction dispute refund", "relevant": ["kb_07"]},
    ]

    algorithms = ["tfidf", "bm25", "query_likelihood"]
    metrics = {alg: {"p_at_3": [], "recall_at_3": [], "ap": [], "rr": []} for alg in algorithms}

    for item in benchmark_queries:
        q = item["query"]
        rel = set(item["relevant"])

        search_methods = {
            "tfidf": engine.search_tfidf(q, top_k=5),
            "bm25": engine.search_bm25(q, top_k=5),
            "query_likelihood": engine.search_query_likelihood(q, top_k=5),
        }

        for alg, results in search_methods.items():
            retrieved_ids = [r["doc_id"] for r in results]
            top3 = retrieved_ids[:3]

            # Precision@3
            p3 = len([d for d in top3 if d in rel]) / 3.0
            metrics[alg]["p_at_3"].append(p3)

            # Recall@3
            rec3 = len([d for d in top3 if d in rel]) / float(len(rel))
            metrics[alg]["recall_at_3"].append(rec3)

            # Average Precision (AP)
            hits = 0
            sum_precisions = 0.0
            for rank, doc_id in enumerate(retrieved_ids, start=1):
                if doc_id in rel:
                    hits += 1
                    sum_precisions += hits / rank
            ap = (sum_precisions / len(rel)) if rel else 0.0
            metrics[alg]["ap"].append(ap)

            # Reciprocal Rank (RR)
            rr = 0.0
            for rank, doc_id in enumerate(retrieved_ids, start=1):
                if doc_id in rel:
                    rr = 1.0 / rank
                    break
            metrics[alg]["rr"].append(rr)

    results = {}
    for alg in algorithms:
        results[alg] = {
            "mean_precision_at_3": round(sum(metrics[alg]["p_at_3"]) / len(benchmark_queries), 3),
            "mean_recall_at_3": round(sum(metrics[alg]["recall_at_3"]) / len(benchmark_queries), 3),
            "MAP": round(sum(metrics[alg]["ap"]) / len(benchmark_queries), 3),
            "MRR": round(sum(metrics[alg]["rr"]) / len(benchmark_queries), 3),
            "F1_at_3": round(
                (2 * (sum(metrics[alg]["p_at_3"]) / len(benchmark_queries)) * (sum(metrics[alg]["recall_at_3"]) / len(benchmark_queries))) /
                max(1e-5, (sum(metrics[alg]["p_at_3"]) / len(benchmark_queries)) + (sum(metrics[alg]["recall_at_3"]) / len(benchmark_queries))),
                3
            )
        }

    return results


# Global singleton instances for knowledge base and security incident logs
kb_engine = InformationRetrievalEngine(BANKING_KNOWLEDGE_BASE)
security_log_engine = InformationRetrievalEngine(SECURITY_INCIDENT_CORPUS)
