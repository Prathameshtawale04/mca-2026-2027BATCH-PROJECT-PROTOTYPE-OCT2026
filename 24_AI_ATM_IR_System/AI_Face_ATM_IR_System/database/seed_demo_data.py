"""Seed demo data for AI Face ATM & Information Retrieval System."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db import get_db, init_db, query_db, execute_db, get_db_path
from services.auth_service import hash_password, hash_pin

def seed_all():
    """Seed comprehensive demo accounts, IR documents, passages, and financial data."""
    print("Initializing SQLite database tables...")
    init_db()

    # Check if database already seeded
    existing_users = query_db("SELECT COUNT(*) as cnt FROM users", one=True)
    if existing_users and existing_users["cnt"] >= 3:
        print("Database already contains demo data. Skipping seeding.")
        return

    print("Seeding demo users and ATM accounts...")
    
    # 1. Seed Demo Users
    demo_users = [
        {
            "username": "admin",
            "email": "admin@atm-system.local",
            "password": "admin123",
            "pin": "9999",
            "role": "admin",
            "full_name": "System Security Admin",
            "account_number": "ADMIN01",
            "balance": 25000.0,
            "daily_limit": 10000.0
        },
        {
            "username": "alex",
            "email": "alex.vance@atm-system.local",
            "password": "password123",
            "pin": "1234",
            "role": "customer",
            "full_name": "Dr. Alex Vance",
            "account_number": "ACC1001",
            "balance": 4850.0,
            "daily_limit": 2000.0
        },
        {
            "username": "elena",
            "email": "elena.rostova@atm-system.local",
            "password": "password123",
            "pin": "5678",
            "role": "customer",
            "full_name": "Elena Rostova",
            "account_number": "ACC1002",
            "balance": 9200.5,
            "daily_limit": 3000.0
        }
    ]

    user_id_map = {}
    account_id_map = {}

    for u in demo_users:
        pwd_hash = hash_password(u["password"])
        pin_hash_val, pin_salt_val = hash_pin(u["pin"])
        res = execute_db(
            """INSERT INTO users (username, email, password_hash, role, full_name, pin_hash, pin_salt)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (u["username"], u["email"], pwd_hash, u["role"], u["full_name"], pin_hash_val, pin_salt_val)
        )
        user_id = res["lastrowid"]
        user_id_map[u["username"]] = user_id

        acc_res = execute_db(
            """INSERT INTO accounts (user_id, account_number, account_type, balance, daily_limit)
               VALUES (?, ?, 'SAVINGS', ?, ?)""",
            (user_id, u["account_number"], u["balance"], u["daily_limit"])
        )
        acc_id = acc_res["lastrowid"]
        account_id_map[u["account_number"]] = acc_id

        # Face metadata
        model_p = f"data/face_data/models/user_{u['account_number']}.yml"
        execute_db(
            """INSERT INTO face_metadata (user_id, account_number, sample_count, model_path, confidence_threshold)
               VALUES (?, ?, 15, ?, 70.0)""",
            (user_id, u["account_number"], model_p)
        )

        # Audit log for creation
        execute_db(
            """INSERT INTO audit_logs (user_id, account_number, event_type, details, ip_address, status)
               VALUES (?, ?, 'SEED_USER', 'Seeded initial demo account', '127.0.0.1', 'SUCCESS')""",
            (user_id, u["account_number"])
        )

    print("Seeding initial transaction history...")
    # Seed Transactions for ACC1001 (Alex)
    alex_acc_id = account_id_map["ACC1001"]
    txs_alex = [
        ("DEPOSIT", 5000.0, 5000.0, "TXN-1001-01", "Initial Payroll Deposit", datetime.now() - timedelta(days=5)),
        ("WITHDRAWAL", 200.0, 4800.0, "TXN-1001-02", "ATM Cash Withdrawal - Branch 04", datetime.now() - timedelta(days=3)),
        ("DEPOSIT", 150.0, 4950.0, "TXN-1001-03", "Cash Deposit - ATM Dispenser", datetime.now() - timedelta(days=2)),
        ("WITHDRAWAL", 100.0, 4850.0, "TXN-1001-04", "ATM Cash Withdrawal - Terminal 12", datetime.now() - timedelta(days=1)),
    ]
    for t_type, amt, bal, ref, desc, dt in txs_alex:
        execute_db(
            """INSERT INTO transactions (account_id, account_number, type, amount, balance_after, reference_no, description, timestamp)
               VALUES (?, 'ACC1001', ?, ?, ?, ?, ?, ?)""",
            (alex_acc_id, t_type, amt, bal, ref, desc, dt.strftime("%Y-%m-%d %H:%M:%S"))
        )

    # Seed Transactions for ACC1002 (Elena)
    elena_acc_id = account_id_map["ACC1002"]
    txs_elena = [
        ("DEPOSIT", 10000.0, 10000.0, "TXN-1002-01", "Wire Transfer Credit", datetime.now() - timedelta(days=6)),
        ("WITHDRAWAL", 500.0, 9500.0, "TXN-1002-02", "Cash Withdrawal - ATM Express", datetime.now() - timedelta(days=4)),
        ("WITHDRAWAL", 299.5, 9200.5, "TXN-1002-03", "Online Utility Bill Debit", datetime.now() - timedelta(days=1)),
    ]
    for t_type, amt, bal, ref, desc, dt in txs_elena:
        execute_db(
            """INSERT INTO transactions (account_id, account_number, type, amount, balance_after, reference_no, description, timestamp)
               VALUES (?, 'ACC1002', ?, ?, ?, ?, ?, ?)""",
            (elena_acc_id, t_type, amt, bal, ref, desc, dt.strftime("%Y-%m-%d %H:%M:%S"))
        )

    print("Seeding personal finance and 50/30/20 budgets...")
    alex_id = user_id_map["alex"]
    # Finance entries for Alex
    current_month = datetime.now().strftime("%Y-%m")
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    finance_items = [
        (alex_id, "INCOME", "Salary", 4500.0, today, "Monthly Research Grant Salary"),
        (alex_id, "EXPENSE", "Housing", 1200.0, today, "Monthly Apartment Rent (Need)"),
        (alex_id, "EXPENSE", "Groceries", 450.0, yesterday, "Supermarket Supplies (Need)"),
        (alex_id, "EXPENSE", "Utilities", 220.0, yesterday, "Electricity and Fiber Internet (Need)"),
        (alex_id, "EXPENSE", "Dining Out", 180.0, two_days_ago, "Weekend Bistro Restaurant (Want)"),
        (alex_id, "EXPENSE", "Entertainment", 95.0, two_days_ago, "Streaming and Gaming Pass (Want)"),
    ]
    for uid, etype, cat, amt, edate, desc in finance_items:
        execute_db(
            """INSERT INTO finance_entries (user_id, entry_type, category, amount, entry_date, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (uid, etype, cat, amt, edate, desc)
        )

    # 50/30/20 budget for Alex
    execute_db(
        """INSERT INTO budgets (user_id, month_year, total_income, needs_budget, wants_budget, savings_budget, notes)
           VALUES (?, ?, 4500.0, 2250.0, 1350.0, 900.0, 'Standard 50/30/20 wealth rule applied.')""",
        (alex_id, current_month)
    )

    # Savings goals for Alex
    execute_db(
        """INSERT INTO savings_goals (user_id, goal_name, target_amount, current_amount, target_date, status)
           VALUES (?, 'Emergency Reserve Fund', 6000.0, 2400.0, '2026-12-31', 'IN_PROGRESS')""",
        (alex_id,)
    )
    execute_db(
        """INSERT INTO savings_goals (user_id, goal_name, target_amount, current_amount, target_date, status)
           VALUES (?, 'High-Yield Investment Certificate', 5000.0, 1500.0, '2027-06-30', 'IN_PROGRESS')""",
        (alex_id,)
    )

    print("Seeding academic IR document corpus (12 documents & passages)...")
    docs = [
        (
            1,
            "Biometric Face Recognition and Security Architecture in Automated Teller Machines",
            "Security & Biometrics",
            "Biometric facial recognition enhances Automated Teller Machine (ATM) security by replacing or augmenting physical magnetic cards and plastic chip credentials. Using OpenCV Haar feature cascades, frontal faces are identified within live optical video feeds. The Local Binary Patterns Histograms (LBPH) algorithm provides spatial texture analysis, computing local binary patterns within circular pixel neighborhoods. Multi-factor authentication requires facial match verification alongside salted cryptographic PIN verification.",
            "Dr. Alex Vance",
            0.18
        ),
        (
            2,
            "Multi-Factor Anti-Spoofing and Liveness Verification in Banking Terminals",
            "Security & Biometrics",
            "Biometric banking kiosks are vulnerable to presentation attacks including printed photographic masks and video replay attacks. Optical anti-spoofing algorithms measure Laplacian high-frequency edge variance to detect blurred or printed paper screens. Skin chrominance filtering in the YCrCb color space distinguishes biological human tissue from synthetic materials, while specular glare detection flags reflections from glass mobile phone displays.",
            "Dr. Alex Vance",
            0.14
        ),
        (
            3,
            "Statistical Language Models: N-grams, Laplace Smoothing, and Perplexity in IR",
            "Language Models",
            "Statistical language models represent probability distributions over word sequences. Unigram, Bigram, and Trigram language models calculate text generation likelihood. To resolve zero-frequency probabilities on unseen terms, additive Laplace smoothing assigns small pseudo-counts to every vocabulary token. Perplexity measures cross-entropy loss, evaluating how well a trained statistical language model predicts a sample test corpus.",
            "Elena Rostova",
            0.16
        ),
        (
            4,
            "Query Likelihood Retrieval: Dirichlet and Jelinek-Mercer Smoothing Approaches",
            "Language Models",
            "The query likelihood model ranks documents by the probability that a document language model generated the user query. Because document-specific models suffer from data sparsity, smoothing interpolates document frequencies with global collection frequencies. Jelinek-Mercer smoothing applies a linear interpolation parameter lambda. Dirichlet prior smoothing employs a Bayesian pseudo-count parameter mu, providing document-length-sensitive smoothing.",
            "Elena Rostova",
            0.15
        ),
        (
            5,
            "Divergence From Randomness (DFR): Probabilistic Models for Document Ranking",
            "Language Models",
            "Divergence From Randomness (DFR) ranking calculates information content by measuring how term frequencies in a document diverge from a random noise distribution. Under the InL2 formulation, term frequencies are normalized against document length, while inverse collection frequencies evaluate term importance. DFR models offer competitive empirical accuracy comparable to BM25 across standard TREC benchmark collections.",
            "Elena Rostova",
            0.12
        ),
        (
            6,
            "Passage Retrieval and Text Segmentation in Dense Document Corpora",
            "Language Models",
            "Long documents often contain isolated sections relevant to a specific user query. Passage retrieval partitions full documents into sliding window segments, preserving sentence boundaries and scoring localized term density. Presenting relevant passages with highlighted search terms accelerates document inspection and enhances precision at top ranks (P@K).",
            "Elena Rostova",
            0.11
        ),
        (
            7,
            "Parallel Query Processing and Distributed Index Architectures in Web Retrieval",
            "Web Retrieval",
            "Web search engines execute thousands of user queries per second across clustered nodes. Parallel query processing distributes search requests across partitioned inverted index shards using multi-threading thread pools. Results from worker shards are merged and re-ranked at the query coordinator, achieving sub-second response times and high system throughput.",
            "System Security Admin",
            0.13
        ),
        (
            8,
            "MapReduce Framework for High-Throughput Inverted Index Construction",
            "Web Retrieval",
            "The MapReduce distributed computing framework enables scalable index construction over petabytes of crawled web content. The Map phase parses HTML tokens and emits intermediate key-value pairs mapping words to document identifiers. The Shuffle and Sort phase groups occurrences by term key, and the Reduce phase consolidates posting lists into a unified inverted index.",
            "System Security Admin",
            0.15
        ),
        (
            9,
            "Link-Based Ranking: The PageRank Algorithm and Random Walk Teleportation",
            "Web Retrieval",
            "The PageRank algorithm computes stationary probability distributions of a random web surfer navigating directed hyperlinks. To prevent dead ends and spider traps, a damping factor alpha (typically 0.85) provides a random teleportation probability. Power iteration updates node rank vectors until convergence, measuring structural authority across the web graph.",
            "System Security Admin",
            0.19
        ),
        (
            10,
            "Collaborative Filtering and Matrix Factorization for Personalized Recommendation",
            "IR Applications",
            "Collaborative filtering systems predict user preferences based on collective historical ratings. User-based collaborative filtering calculates similarity between customer profiles using Pearson correlation or cosine coefficients. Matrix factorization decomposes sparse user-item interaction matrices into low-dimensional latent feature embeddings, resolving cold-start and sparsity challenges.",
            "Dr. Alex Vance",
            0.12
        ),
        (
            11,
            "Content-Based Filtering and Knowledge-Based Recommender Systems in Finance",
            "IR Applications",
            "Content-based recommender systems construct user preference vectors from term frequencies (TF-IDF) of previously inspected items. In financial advisory applications, knowledge-based recommenders use explicit business logic constraints and financial suitability rules (e.g., liquidity requirements, risk tolerance, and APY returns) rather than relying on historical interaction matrices.",
            "Dr. Alex Vance",
            0.10
        ),
        (
            12,
            "Information Extraction and Semantic Web Knowledge Graphs with RDF Triples",
            "IR Applications",
            "Information extraction identifies entities and relationships from unstructured web text, converting natural language into Subject-Predicate-Object (SPO) triples. Semantic knowledge graphs represent domain facts as directed labeled graphs, enabling ontology-driven reasoning, linked data queries, and verifiable knowledge integration across heterogeneous banking data sources.",
            "Dr. Alex Vance",
            0.14
        )
    ]

    for doc_id, title, cat, content, author, pr_score in docs:
        execute_db(
            """INSERT INTO documents (doc_id, title, category, content, author, pagerank_score)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (doc_id, title, cat, content, author, pr_score)
        )

        # Seed passages (split content into 2 segments)
        sentences = content.split(". ")
        mid = len(sentences) // 2
        p1 = ". ".join(sentences[:mid]) + "."
        p2 = ". ".join(sentences[mid:])
        execute_db(
            """INSERT INTO passages (doc_id, passage_index, content, start_char, end_char)
               VALUES (?, 1, ?, 0, ?)""",
            (doc_id, p1, len(p1))
        )
        if p2.strip():
            execute_db(
                """INSERT INTO passages (doc_id, passage_index, content, start_char, end_char)
                   VALUES (?, 2, ?, ?, ?)""",
                (doc_id, p2, len(p1) + 1, len(content))
            )

    print("Seeding inverted index entries...")
    # Build initial inverted index for sample terms
    for doc_id, _, _, content, _, _ in docs:
        words = [w.strip(".,;:()").lower() for w in content.split() if len(w) > 3]
        term_counts = {}
        for w in words:
            term_counts[w] = term_counts.get(w, 0) + 1
        for term, freq in term_counts.items():
            execute_db(
                """INSERT INTO inverted_index (term, doc_id, term_frequency)
                   VALUES (?, ?, ?)""",
                (term, doc_id, freq)
            )

    print("Seeding semantic knowledge triples and user interactions...")
    triples = [
        ("Face Recognition", "enhances", "ATM Security", 1.0, 1),
        ("ATM Security", "employs", "Multi-Factor Authentication", 0.95, 1),
        ("Multi-Factor Authentication", "combines", "Biometrics and PIN", 0.98, 2),
        ("Anti-Spoofing", "measures", "Laplacian Variance", 0.92, 2),
        ("Language Models", "estimate", "Query Likelihood", 0.96, 4),
        ("Query Likelihood", "requires", "Dirichlet Smoothing", 0.90, 4),
        ("Web Retrieval", "applies", "PageRank Algorithm", 0.95, 9),
        ("PageRank", "computes", "Link Authority", 0.94, 9),
        ("Collaborative Filtering", "computes", "User Similarity", 0.91, 10),
        ("Content-Based Filtering", "matches", "TF-IDF Vectors", 0.89, 11),
        ("Knowledge Graph", "structures", "RDF Triples", 0.97, 12),
        ("MapReduce", "builds", "Inverted Index", 0.93, 8),
    ]
    for subj, pred, obj, conf, s_doc in triples:
        execute_db(
            """INSERT INTO knowledge_triples (subject, predicate, object, confidence, source_doc_id)
               VALUES (?, ?, ?, ?, ?)""",
            (subj, pred, obj, conf, s_doc)
        )

    # Collaborative filtering interactions (Alex and Elena ratings on documents)
    interactions = [
        (alex_id, 1, 5.0),
        (alex_id, 2, 4.5),
        (alex_id, 3, 4.0),
        (alex_id, 10, 5.0),
        (alex_id, 11, 4.5),
        (user_id_map["elena"], 3, 5.0),
        (user_id_map["elena"], 4, 5.0),
        (user_id_map["elena"], 5, 4.5),
        (user_id_map["elena"], 7, 4.0),
        (user_id_map["elena"], 9, 5.0),
        (user_id_map["admin"], 1, 4.0),
        (user_id_map["admin"], 7, 5.0),
        (user_id_map["admin"], 8, 5.0),
        (user_id_map["admin"], 9, 4.5),
    ]
    for uid, did, rating in interactions:
        execute_db(
            """INSERT INTO user_interactions (user_id, doc_id, rating, interaction_type)
               VALUES (?, ?, ?, 'RATING')""",
            (uid, did, rating)
        )

    # Crawl pages and link graph for PageRank
    crawl_samples = [
        ("http://atm-security.edu/home", "ATM Security Architecture Portal", "Overview of biometric banking and secure ATM terminal design.", 200, 0),
        ("http://atm-security.edu/biometrics", "Biometric Authentication Standards", "Detailed guidelines on facial recognition and anti-spoofing.", 200, 1),
        ("http://atm-security.edu/cryptography", "PIN Encryption and PBKDF2 Standards", "Cryptographic PIN hashing algorithms for banking networks.", 200, 1),
        ("http://ir-research.org/lms", "Language Models in Retrieval", "Statistical language models and Dirichlet smoothing principles.", 200, 0),
        ("http://ir-research.org/pagerank", "Link Analysis and PageRank", "Directed graph ranking and web hyperlink topology.", 200, 1),
    ]
    for url, title, text, sc, dp in crawl_samples:
        execute_db(
            """INSERT INTO crawl_pages (url, title, content_text, status_code, depth)
               VALUES (?, ?, ?, ?, ?)""",
            (url, title, text, sc, dp)
        )

    link_edges = [
        ("http://atm-security.edu/home", "http://atm-security.edu/biometrics"),
        ("http://atm-security.edu/home", "http://atm-security.edu/cryptography"),
        ("http://atm-security.edu/biometrics", "http://atm-security.edu/cryptography"),
        ("http://atm-security.edu/cryptography", "http://atm-security.edu/home"),
        ("http://ir-research.org/lms", "http://ir-research.org/pagerank"),
        ("http://ir-research.org/pagerank", "http://ir-research.org/lms"),
        ("http://atm-security.edu/home", "http://ir-research.org/lms"),
    ]
    for src_u, dst_u in link_edges:
        execute_db(
            """INSERT INTO links (source_url, target_url, weight)
               VALUES (?, ?, 1.0)""",
            (src_u, dst_u)
        )

    print("Demo database successfully initialized and seeded!")

if __name__ == "__main__":
    seed_all()
