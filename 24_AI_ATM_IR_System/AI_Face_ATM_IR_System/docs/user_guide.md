# User Guide: AI-Based Face Recognition ATM Security and Intelligent Information Retrieval System

Welcome to the application! This guide will help you navigate and use the various features of the system.

## 1. Getting Started

The application is a web-based system running locally on your machine. You can access it by opening your web browser and navigating to:
**http://127.0.0.1:5000** (or localhost:5000)

### Demo Accounts

The database has been seeded with demo accounts for you to test the system.

**ATM User Account:**
*   **Account Number:** ACC1001
*   **PIN:** 1234
*   *(Note: The face recognition model for this demo user is synthetically generated).*

**Admin Account:**
*   **Account Number:** ADMIN01
*   **PIN:** 9999

## 2. Navigation

The sidebar on the left provides access to all modules in the system. Note that academic "Unit" names have been removed for a cleaner user experience.

### Main Modules:

*   **Dashboard:** System overview, statistics, and quick links.
*   **ATM Operations (Security):** The Face Recognition ATM interface.
*   **Language Models:** Explore N-grams, Automaton, and DFR algorithms.
*   **Search & Retrieval:** The Hybrid Search engine.
*   **Web Retrieval:** Web crawling, MapReduce, and PageRank simulations.
*   **Recommendations:** Collaborative and Content-based filtering demos.
*   **Knowledge Graph:** Visual representation of entities and relationships.
*   **System Architecture:** Overview of the technology stack and architecture.

## 3. Module Details

### Face Recognition ATM
1.  Navigate to **ATM Operations**.
2.  The system will attempt to access your webcam (ensure permissions are granted).
3.  Enter the Account Number (`ACC1001`) and PIN (`1234`).
4.  Click **Authenticate**. The system will verify the PIN and simulate a face check against the stored model.
5.  Once authenticated, you can perform simulated Deposit, Withdrawal, and Balance Inquiry operations.

### Search & Retrieval
1.  Navigate to **Search & Retrieval**.
2.  Enter a query in the search bar (e.g., "ATM security", "Information retrieval").
3.  Adjust the sliders to change the weighting of different scoring models (TF-IDF, PageRank, Semantic, DFR).
4.  Click **Search** to view the dynamically ranked results.

### Language Models
1.  Navigate to **Language Models**.
2.  Enter a sample text.
3.  Select the desired N-gram size (e.g., 2 for Bigrams) and click **Analyze** to see frequency counts.
4.  Switch to the **Divergence from Randomness (DFR)** tab to see DFR term scoring for a given text.

### Web Retrieval (Crawling & PageRank)
1.  Navigate to **Web Retrieval**.
2.  **Web Crawler:** Enter a seed URL (e.g., `https://en.wikipedia.org/wiki/Information_retrieval`), set a depth limit, and click **Start Crawl**. (Note: Be respectful of website rate limits).
3.  **PageRank:** Click **Calculate PageRank** to view simulated network graphs and node importance scores.
4.  **MapReduce:** Enter a large block of text to simulate distributed word counting.

### Recommendations
1.  Navigate to **Recommendations**.
2.  **Collaborative Filtering:** Enter a User ID (e.g., 1 or 2) to see document recommendations based on user-item interaction matrices.
3.  **Content-Based:** Enter a Document ID to find similar documents based on TF-IDF cosine similarity.

### Knowledge Graph
1.  Navigate to **Knowledge Graph**.
2.  The page will render an interactive network graph based on RDF-style triples stored in the database (e.g., Node A -[relationship]-> Node B).
3.  You can interact with the graph nodes using your mouse.

## 4. Troubleshooting

*   **Webcam Not Working:** Ensure your browser has permission to access the camera. If using HTTP instead of HTTPS, some browsers might block webcam access. The local environment (127.0.0.1) usually bypasses this, but keep it in mind.
*   **Application Crash:** Check the terminal window where you ran `python app.py` for error traces.
*   **Database Issues:** If the database becomes corrupted or you want to start fresh, delete `database/atm_ir.db` and re-run `python database/seed_data.py`.
