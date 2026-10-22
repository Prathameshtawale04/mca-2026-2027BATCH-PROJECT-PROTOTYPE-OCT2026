import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import cv2
import numpy as np
from database.db import init_db, transaction, execute_sql, query_all
from face_atm.security_service import generate_salt, hash_pin, log_security_event
from face_atm.face_recognizer import LBPHFaceManager
from config import Config

SEED_USERS = [
    {
        "account_number": "ACC1001",
        "full_name": "Dr. Alex Vance",
        "email": "alex.vance@academic-bank.edu",
        "pin": "1234",
        "balance": 4850.00,
        "type": "PREMIUM_SAVINGS"
    },
    {
        "account_number": "ACC1002",
        "full_name": "Elena Rostova",
        "email": "elena.rostova@academic-bank.edu",
        "pin": "5678",
        "balance": 9200.50,
        "type": "CHECKING"
    },
    {
        "account_number": "ADMIN01",
        "full_name": "System Security Administrator",
        "email": "admin@academic-bank.edu",
        "pin": "9999",
        "balance": 25000.00,
        "type": "ADMIN_OVERRIDE"
    }
]

SEED_DOCUMENTS = [
    {
        "title": "Biometric ATM Security Architecture Using Face Recognition",
        "category": "Biometrics & Security",
        "content": "Automated Teller Machines (ATMs) require robust physical and digital security. Traditional ATM card and PIN mechanisms are susceptible to card skimming, shoulder surfing, and physical theft. By integrating computer vision algorithms such as Haar Cascade frontal face detection and Local Binary Patterns Histograms (LBPH), the ATM captures facial frames during card insertion. A multi-frame verification pipeline confirms biometric authenticity before prompting for PIN entry, drastically curtailing unauthorized cash withdrawals.",
        "author": "Dr. Alex Vance"
    },
    {
        "title": "Local Binary Patterns Histograms (LBPH) for Real-Time Facial Recognition",
        "category": "Computer Vision",
        "content": "The LBPH algorithm operates by thresholding the 3x3 neighborhood of each pixel in a grayscale face image. By comparing pixel intensities against center values, binary numbers are generated and converted to decimal values. The face image is divided into a grid of cells, and histograms of pixel patterns are extracted from each cell and concatenated into an invariant feature vector. LBPH provides high computational efficiency and resilience against monotonic illumination variations in embedded banking kiosks.",
        "author": "Prof. Marcus Thorne"
    },
    {
        "title": "Cryptographic PIN Hashing with PBKDF2 and Salted Key Derivation",
        "category": "Cybersecurity",
        "content": "Password-Based Key Derivation Function 2 (PBKDF2) applies a pseudorandom function along with an HMAC-SHA256 hash algorithm to the input PIN string across 100000 iterations with a cryptographic salt. This computationally intensive derivation prevents rainbow table lookups and mitigates hardware-accelerated dictionary attacks. Furthermore, modern ATM security policies enforce temporary account lockouts after three consecutive failed attempts.",
        "author": "Elena Rostova"
    },
    {
        "title": "Language Models for Information Retrieval: Unigram, Bigram, and Trigram",
        "category": "Information Retrieval",
        "content": "Statistical language models in Information Retrieval treat each document as a generative language source. Under the Unigram model, word occurrences are assumed independent. Bigram and Trigram models incorporate conditional probability of adjacent words using Markov chain assumptions. Smoothing methods such as Laplace add-one and Jelinek-Mercer interpolation assign non-zero probabilities to unseen n-grams, enabling accurate perplexity scoring and sentence generation evaluation.",
        "author": "Dr. Sarah Lin"
    },
    {
        "title": "Divergence From Randomness (DFR) Ranking Framework in Text Retrieval",
        "category": "Information Retrieval",
        "content": "The Divergence From Randomness (DFR) framework models term weights based on the divergence of term frequency from that expected under a purely random distribution of words. By measuring the information gain of finding a term in a document compared to the collection, DFR utilizes first normalization (such as L2 for document length variation) and second normalization (Laplace after-effect) to yield superior ranking effectiveness on structured financial corpora.",
        "author": "Dr. Sarah Lin"
    },
    {
        "title": "Passage Retrieval and Sliding Window Text Segmentation",
        "category": "Information Retrieval",
        "content": "When documents exceed several thousand words, full-document retrieval often dilutes localized relevance. Passage retrieval segments text into overlapping windows of sentences or fixed-length word blocks. Query terms are matched against individual passages, allowing the search engine to pinpoint the precise paragraph that answers the user inquiry and highlight matched terminology for rapid human scanning.",
        "author": "Prof. Marcus Thorne"
    },
    {
        "title": "PageRank and Structural Link Analysis in Directed Web Graphs",
        "category": "Web Retrieval",
        "content": "The PageRank algorithm models web surfing behavior as a Markov chain over a directed graph of hyperlinks. Nodes represent documents and edges represent hyperlinked citations. Through power iteration with a damping factor of 0.85, PageRank distributes stationary probability across pages. Pages receiving incoming links from reputable hubs attain higher authority scores, mitigating search manipulation.",
        "author": "Dr. Sarah Lin"
    },
    {
        "title": "MapReduce Parallel Computing for Distributed Inverted Indexing",
        "category": "Distributed Systems",
        "content": "The MapReduce programming model enables scalable parallel indexing over vast document collections. In the Map phase, worker nodes tokenize documents into intermediate key-value pairs (word, doc_id, 1). During the Shuffle and Sort phase, pairs with identical keys are grouped. The Reduce phase aggregates occurrences into compact posting lists, constructing an enterprise inverted index across distributed clusters.",
        "author": "Elena Rostova"
    },
    {
        "title": "User-Based Collaborative Filtering in Financial Recommenders",
        "category": "Recommender Systems",
        "content": "Collaborative filtering predicts a user's interest in banking resources and security alerts by collecting preference ratings from an active community. By calculating cosine similarity between user rating vectors, nearest neighbors are identified. Unseen items are rated via weighted sum prediction, providing personalized recommendations without requiring prior domain metadata.",
        "author": "Dr. Alex Vance"
    },
    {
        "title": "Content-Based Recommendation Systems Using Vector Space Models",
        "category": "Recommender Systems",
        "content": "Content-based filtering recommends items based on the lexical and semantic similarity between document content and a user's reading history. TF-IDF feature vectors represent both documents and user profiles in a high-dimensional vector space. Cosine similarity determines thematic alignment, ensuring that viewing an article on ATM face recognition leads to recommendations of biometric security architectures.",
        "author": "Dr. Alex Vance"
    },
    {
        "title": "Semantic Web Knowledge Graphs and RDF Triples for Banking Ontologies",
        "category": "Semantic Web",
        "content": "The Semantic Web enhances unstructured data with explicit meaning through the Resource Description Framework (RDF). Knowledge is structured as Subject-Predicate-Object triples, such as (ATM System, uses, Face Recognition) and (Face Recognition, provides, Biometric Authentication). Graph databases and NetworkX facilitate multi-hop inference, link prediction, and relationship visualization.",
        "author": "Elena Rostova"
    },
    {
        "title": "Polite Web Crawling Architecture and BeautifulSoup Parsing",
        "category": "Web Crawling",
        "content": "A production-grade web crawler consists of a URL frontier queue, DNS resolver, downloader module, HTML parser, and visited URL set. Adhering to robots.txt guidelines and polite crawl delays prevents server denial-of-service. BeautifulSoup extracts DOM trees, isolating titles, headings, anchor hyperlinks, and body paragraphs for downstream information extraction.",
        "author": "Prof. Marcus Thorne"
    }
]

SEED_TRIPLES = [
    ("ATM System", "uses", "Face Recognition"),
    ("Face Recognition", "extracts", "LBPH Biometric Features"),
    ("Face Recognition", "provides", "Biometric Authentication"),
    ("Biometric Authentication", "improves", "Banking Security"),
    ("Banking Security", "prevents", "Fraudulent Withdrawals"),
    ("ATM System", "verifies", "PBKDF2 Hashed PIN"),
    ("PBKDF2 Hashed PIN", "protects", "User Bank Account"),
    ("Search Engine", "indexes", "Inverted Index"),
    ("Inverted Index", "accelerates", "Query Processing"),
    ("PageRank", "analyzes", "Hyperlink Graph"),
    ("PageRank", "calculates", "Document Authority"),
    ("Information Retrieval", "ranksWith", "Language Model Query Likelihood"),
    ("Information Retrieval", "evaluatesWith", "MAP and Precision@K"),
    ("Collaborative Filtering", "predicts", "User Document Preferences"),
    ("Content-Based Filtering", "computes", "TF-IDF Cosine Similarity"),
    ("Knowledge Graph", "represents", "Semantic Triples")
]

SEED_INTERACTIONS = [
    ("ACC1001", 1, 5.0), ("ACC1001", 2, 4.5), ("ACC1001", 3, 5.0), ("ACC1001", 4, 3.0),
    ("ACC1002", 1, 4.0), ("ACC1002", 3, 5.0), ("ACC1002", 7, 4.5), ("ACC1002", 8, 4.0),
    ("ADMIN01", 2, 5.0), ("ADMIN01", 5, 4.0), ("ADMIN01", 9, 5.0), ("ADMIN01", 11, 4.5)
]

def seed_synthetic_face_samples(account_number: str):
    """
    Generates synthetic grayscale face samples with gradient and eye/mouth geometry
    so that LBPH recognizer can train and function out of the box even without a live webcam.
    """
    manager = LBPHFaceManager()
    samples_dir = manager.get_samples_dir(account_number)
    
    if len(list(samples_dir.glob("*.jpg"))) >= 10:
        return

    # Seed 15 synthetic biometric sample variations
    np.random.seed(hash(account_number) % 100000)
    for i in range(15):
        # Base oval face
        img = np.zeros((200, 200), dtype=np.uint8)
        # Gradient
        for y in range(200):
            val = int(np.clip(120 + int((y - 100) * 0.2), 40, 220))
            img[y, :] = val
        # Face ellipse
        cv2.ellipse(img, (100, 100), (60, 80), 0, 0, 360, 180, -1)
        # Eyes
        cv2.circle(img, (75, 80), 10, 50, -1)
        cv2.circle(img, (125, 80), 10, 50, -1)
        # Nose
        cv2.line(img, (100, 85), (100, 115), 70, 3)
        # Mouth
        cv2.ellipse(img, (100, 140), (25, 12), 0, 0, 180, 60, 3)
        
        # Add slight random noise for realistic variations
        noise = np.random.normal(0, 3, img.shape).astype(np.int16)
        noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        cv2.imwrite(str(samples_dir / f"sample_{i:03d}.jpg"), noisy)

    # Train model
    manager.train_user_model(account_number)

def run_seed():
    from database.seed_demo_data import seed_all
    seed_all()

    # 2. Seed IR Documents
    existing_docs = query_all("SELECT doc_id FROM documents")
    if len(existing_docs) < len(SEED_DOCUMENTS):
        for doc in SEED_DOCUMENTS:
            execute_sql(
                """
                INSERT INTO documents (title, category, content, author)
                VALUES (?, ?, ?, ?)
                """,
                (doc["title"], doc["category"], doc["content"], doc["author"])
            )

    # 3. Seed Knowledge Triples
    existing_triples = query_all("SELECT id FROM knowledge_triples")
    if len(existing_triples) < len(SEED_TRIPLES):
        for s, p, o in SEED_TRIPLES:
            execute_sql(
                """
                INSERT INTO knowledge_triples (subject, predicate, object, confidence)
                VALUES (?, ?, ?, 0.95)
                """,
                (s, p, o)
            )

    # 4. Seed User Interactions
    existing_inter = query_all("SELECT id FROM user_interactions")
    if len(existing_inter) < len(SEED_INTERACTIONS):
        for u_acc, d_id, rating in SEED_INTERACTIONS:
            execute_sql(
                """
                INSERT INTO user_interactions (account_number, doc_id, rating)
                VALUES (?, ?, ?)
                """,
                (u_acc, d_id, rating)
            )

    print("Database initialization and seed completed successfully.")

if __name__ == "__main__":
    run_seed()
