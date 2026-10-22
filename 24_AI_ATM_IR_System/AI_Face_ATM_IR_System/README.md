# Intelligent Face Recognition ATM Security, Financial Assistance and Information Retrieval System

> **A Master-Level Engineering Application Integrating Biometric Computer Vision, Multi-Factor Banking Security, Statistical Language Modeling, Distributed Web Retrieval, and Semantic Recommender Systems.**

[![Tests](https://img.shields.io/badge/tests-88%20passed%20(100%25)-success)](file:///b:/SY_Projects/AI_Face_ATM_IR_System/tests/)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-3.1-black)](https://palletsprojects.com/p/flask/)
[![OpenCV](https://img.shields.io/badge/opencv-4.10-red)](https://opencv.org/)
[![Database](https://img.shields.io/badge/database-SQLite%20ACID-blue)](file:///b:/SY_Projects/AI_Face_ATM_IR_System/data/atm_system.db)

---

## 1. Project Abstract & Architectural Overview

Modern physical ATM terminals demand resilient multi-factor biometric authentication to defeat credential stuffing, physical skimming, and identity spoofing. Concurrently, financial research and compliance organizations require high-throughput information retrieval systems capable of searching heterogeneous banking legislation, threat advisories, and knowledge graphs.

This project delivers a **single, unified, end-to-end Flask application** that runs entirely locally at `http://127.0.0.1:5000`:
1. **Biometric Face Recognition & Anti-Spoofing**: Real-time webcam face capture using OpenCV Haar Cascades, Local Binary Patterns Histograms (LBPH) facial recognition, optical anti-spoofing liveness verification (Laplacian micro-texture variance $\ge 45.0$), and salted PBKDF2 HMAC-SHA256 PIN cryptography with automated 3-strike card lockouts.
2. **ATM Hardware Simulation**: Tactile cash withdrawal with physical banknote dispenser tray ($100, $50, $20, $10 denominations), atomic deposit transactions, mini-statements, and tamper-resistant security audit trails.
3. **50/30/20 Smart Financial Intelligence**: Automated monthly ledger breakdown (50% Needs, 30% Wants, 20% Wealth), rule-based guidance engine, and interactive savings vaults.
4. **Unit IV: Language Models for Information Retrieval**: Deterministic Finite Automata (DFA) Boolean query parsing, N-gram language models (Unigram, Bigram, Trigram) with Laplace smoothing and Perplexity evaluation, Query Likelihood with Dirichlet ($\mu$) and Jelinek-Mercer ($\lambda$) smoothing, Divergence From Randomness (DFR InL2), and sliding window passage retrieval with keyword highlighting.
5. **Unit V: Web Retrieval, Distributed Systems & Web Crawling**: Iterative PageRank power algorithm ($\alpha=0.85$), local MapReduce inverted indexer simulation (Map, Shuffle, Reduce), parallel shard query coordinator (`concurrent.futures`), and a polite BeautifulSoup crawler with robots and depth limits.
6. **Unit VI: IR Applications & Semantic Web**: User-based Collaborative Filtering utility matrix, Content-based TF-IDF cosine recommender, Knowledge-based rule inference engine, NLP entity and Subject-Predicate-Object (SPO) triple extractor, and an interactive Vis.js RDF knowledge graph explorer.
7. **Multi-Model Hybrid Score Fusion Search**: Weighted fusion across Language Models, Vector Space Model (TF-IDF), DFR, and PageRank with real-time sliders and explainable component score breakdowns.
8. **Administrator Security Operations Center (SOC)**: Real-time user management, 1-click account freeze/unfreeze toggles, balance overrides, and live security telemetry streams.

---

## 2. System Architecture

```
                             ┌───────────────────────────────────────┐
                             │       Unified Flask Application       │
                             │         http://127.0.0.1:5000         │
                             └──────────────────┬────────────────────┘
                                                │
         ┌────────────────────────┬─────────────┴───────────┬────────────────────────┐
         ▼                        ▼                         ▼                        ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│ Face ATM Security │    │  Language Models  │    │   Web Retrieval   │    │  IR Applications  │
│  - Haar Cascade   │    │  - DFA Automaton  │    │  - Iterative PR   │    │  - Collaborative  │
│  - LBPH Recog.    │    │  - N-gram Perplex │    │  - MapReduce      │    │  - Content-Based  │
│  - PBKDF2 Hashing │    │  - Dirichlet LM   │    │  - Parallel Shards│    │  - Rule Inference │
│  - Dispenser Tray │    │  - DFR (InL2)     │    │  - Polite Crawler │    │  - SPO Triples    │
│  - Audit Logs     │    │  - Passage Search │    │  - Mini VSM Index │    │  - Vis.js Graph   │
└─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘
          │                        │                        │                        │
          └────────────────────────┼────────────────────────┼────────────────────────┘
                                   ▼                        ▼
                      ┌──────────────────────────────────────────────┐
                      │    Unified Multi-Model Hybrid Search Engine  │
                      │  Score = w1*LM + w2*TFIDF + w3*DFR + w4*PR   │
                      └──────────────────────┬───────────────────────┘
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │     SQLite ACID Database (atm_system.db)     │
                      │   13 Normalized Tables with Foreign Keys     │
                      └──────────────────────────────────────────────┘
```

---

## 3. Technology Stack

* **Web Framework & Backend**: Python 3.11+, Flask 3.1, Jinja2 Templates, Werkzeug Security.
* **Database & Persistence**: SQLite 3 with strict ACID transactions, foreign keys enabled (`PRAGMA foreign_keys = ON`), and parameterized queries.
* **Computer Vision & Biometrics**: OpenCV (`cv2`) 4.10, Haar Cascade Classifier (`haarcascade_frontalface_default.xml`), Local Binary Patterns Histograms (`cv2.face.LBPHFaceRecognizer`), Laplacian variance anti-spoofing.
* **Data Processing & Information Retrieval**: NumPy, Scikit-learn (TF-IDF vectorizer, cosine similarity), NetworkX (Directed graph PageRank & Knowledge Web).
* **Frontend UI & Visualization**: Bootstrap 5 Cyber-Banking Dark Theme, FontAwesome 6 Icons, Chart.js (financial and perplexity charts), Vis-Network (interactive RDF graph visualization).
* **Testing & Verification**: Pytest 8.3 / 9.1 with automated test discovery and isolated test databases.

---

## 4. Installation & Setup (Windows PowerShell)

### Prerequisites
* Windows 10 or 11
* Python 3.11, 3.12, or 3.13 installed and added to `PATH`
* Visual Studio Code or your preferred IDE
* Physical webcam (Optional — system includes pre-seeded biometric models for 1-click viva evaluation)

### Step 1: Open Windows PowerShell and Navigate to Project
```powershell
cd B:\SY_Projects\AI_Face_ATM_IR_System
```

### Step 2: Create and Activate Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts execution scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Verify Database & Pre-Seed Demo Accounts
```powershell
python database/seed_demo_data.py
```
*(Note: If you run `python app.py` directly, the system automatically detects, initializes, and seeds missing tables on startup).*

### Step 5: Run the Complete Automated Test Suite (88 Test Cases)
```powershell
python -m pytest tests/ -v
```
**Expected Output:** `88 passed in ~130s (100% Pass Rate)`.

### Step 6: Start the Application Server
```powershell
python app.py
```

### Step 7: Access the System
Open your web browser and navigate to:
**[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 5. Seeded Demo Accounts & Credentials

| Role | Username | Password | Account Number | PIN | Balance | Features & Access |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Customer** | `alex` | `password123` | `ACC1001` | `1234` | \$4,850.00 | Checking & Savings, ATM Terminal, Face Biometrics, Personal Finance, Hybrid Search |
| **Customer** | `elena` | `password123` | `ACC1002` | `5678` | \$9,200.50 | Checking & Savings, ATM Terminal, Face Biometrics, Personal Finance, Hybrid Search |
| **Administrator** | `admin` | `admin123` | `ADMIN01` | `9999` | \$25,000.00 | Security Operations Center (SOC), Lock/Unlock Users, Adjust Balances, Audit Trail |

> **Viva Evaluation Shortcut**: The login page provides **1-Click Quick Demo Login Buttons** (`Alex Vance`, `Elena Rostova`, `Admin SOC`) to instantly test user sessions without manual typing or webcam camera setup.

---

## 6. Complete Feature-by-Feature Demonstration Guide

### Module 1: Dashboard & Authentication
* **URL**: `http://127.0.0.1:5000/` and `/login`
* **Features**:
  * Dual-mode authentication (Username/Password and 1-Click Demo).
  * Collapsible 12-section sidebar navigation with responsive layout.
  * Executive KPI metric cards (Available Balance, Security Trust Score, Recent Transactions).
  * Automated account lockout after 5 consecutive invalid password attempts.

### Module 2: Face Biometrics & Optical Anti-Spoofing
* **URL**: `/face/enroll` and `/face/verify`
* **Features**:
  * Real-time HTML5 webcam canvas frame capture with cyan HUD target reticle.
  * Real OpenCV Haar Cascade frontal face detection.
  * Optical liveness verification: Laplacian variance texture check ($\ge 45.0$) to detect blurry phone-screen attacks.
  * Dynamic Local Binary Patterns Histograms (LBPH) training and distance threshold verification ($\le 70.0$).
  * Automatic on-the-fly model training fallback if model cache is cleared.
  * Revoke and purge biometric face samples with secure data deletion.

### Module 3: ATM Hardware Simulation Core
* **URL**: `/atm`
* **Features**:
  * Tactile interactive on-screen ATM keypad with audio synthesis feedback.
  * Salted PBKDF2 HMAC-SHA256 PIN authentication with automated 3-strike card lockout policy.
  * Atomic cash withdrawals with instant balance verification.
  * Physical cash dispenser tray displaying exact banknote bill breakdown ($100, $50, $20, $10).
  * Mini-statement view displaying recent transactions with timestamps and balance tracking.

### Module 4: Personal Finance & 50/30/20 Budgeting
* **URL**: `/finance`
* **Features**:
  * Real-time Income and Expense logging ledger with customizable categories.
  * Mathematical 50/30/20 Wealth Formula calculation:
    $$\text{Needs} \le 50\%, \quad \text{Wants} \le 30\%, \quad \text{Savings} \ge 20\%$$
  * Dynamic Chart.js financial health doughnut charts.
  * Rule-based financial advisor tips recommending specific dollar allocations.
  * Savings Goal Vaults with deposit contributions and animated progress bars.

### Module 5: Unit IV — Language Models for Information Retrieval
* **URL**: `/ir/language_models`
* **Features**:
  * **Deterministic Finite Automata (DFA)**: Live Boolean query state transition parser with syntactic token visualization.
  * **N-gram Language Models**: Unigram, Bigram, and Trigram probabilities with Laplace $(+1)$ smoothing and Perplexity calculation.
  * **Multinomial Distributions**: Document term generation probability metrics.
  * **Query Likelihood Retrieval**: Dirichlet Prior smoothing ($\mu = 1500$) and Jelinek-Mercer interpolation ($\lambda = 0.7$).
  * **Divergence From Randomness (DFR)**: InL2 hypergeometric term-weighting ranking model.
  * **Sliding Window Passage Retrieval**: Configurable window passage extraction with yellow keyword highlighting.

### Module 6: Unit V — Web Retrieval, Distributed Systems & Crawling
* **URL**: `/ir/web_retrieval`
* **Features**:
  * **Iterative PageRank**: Live power iteration calculation with random walk teleportation ($\alpha = 0.85$) and residual convergence history.
  * **MapReduce Framework**: Interactive 3-stage Map, Shuffle, and Reduce simulation indexing banking documents into inverted postings.
  * **Parallel Shard Coordinator**: Multi-threaded query distribution across 3 distinct shard worker nodes using Python `concurrent.futures`.
  * **Polite Web Crawler**: Live crawler simulation with politeness delays, maximum depth limits, and URL discovery tables.

### Module 7: Unit VI — IR Applications & Semantic Web
* **URL**: `/ir/applications`
* **Features**:
  * **User-Based Collaborative Filtering**: User-item utility interaction matrix with Pearson correlation and cosine neighborhood calculations.
  * **Content-Based Recommender**: TF-IDF document profiling with cosine similarity matrix matches.
  * **Knowledge-Based Rules Engine**: Multi-attribute rule inference recommending banking whitepapers based on technology and application domain.
  * **NLP Information Extraction**: Real-time technology Named Entity Recognition (NER) and Subject-Predicate-Object (SPO) triple generation.
  * **Interactive Knowledge Graph**: Vis.js interactive graph canvas rendering RDF semantic nodes, edges, and entity relationships.

### Module 8: Unified Multi-Model Hybrid Search Engine
* **URL**: `/search/hybrid` and `/search/history`
* **Features**:
  * Live multi-model score fusion integrating Language Models, Vector Space Model (TF-IDF), DFR, and PageRank:
    $$S_{\text{hybrid}}(d, q) = w_1 S_{\text{LM}} + w_2 S_{\text{TF-IDF}} + w_3 S_{\text{DFR}} + w_4 S_{\text{PageRank}}$$
  * Real-time interactive weight sliders with dynamic score recalculation.
  * Transparent component score badges explaining why each document was ranked.
  * Search telemetry history logged into `search_history` with query latency tracking.

### Module 9: Administrator Security Operations Center (SOC)
* **URL**: `/admin`
* **Features**:
  * Accessible exclusively to `admin` accounts (enforced by `@admin_required` decorator).
  * System-wide security KPIs (Total Users, Active Vaults, Security Incidents, Inverted Docs).
  * 1-Click User Account Lock / Unlock toggles that immediately take effect.
  * Administrator balance override control.
  * Live security audit trail inspector tracking all login, face recognition, and transaction events.

### Module 10: Mira AI Financial Copilot
* **URL**: `/mira/chat`
* **Features**:
  * Conversational banking assistant supporting real-time account inquiries, budget guidance, and IR navigation.
  * Intent-classification rules for balance lookups, ATM guidelines, and information retrieval recommendations.

### Module 11: Analytics & IR Evaluation Metrics
* **URL**: `/analytics`
* **Features**:
  * Standard Information Retrieval evaluation metrics: Precision, Recall, F1-Score, Precision@K ($P@5, P@10$), and Mean Average Precision (MAP).
  * Performance charts visualizing ranking efficiency.

### Module 12: Academic Syllabus Coverage
* **URL**: `/syllabus`
* **Features**:
  * Comprehensive matrix cross-referencing all course curriculum topics with source code files and demonstration workbenches.

---

## 7. Curriculum & Syllabus Implementation Matrix

| Curriculum Unit | Topic | Source Code Implementation | Test File | Verification |
| :--- | :--- | :--- | :--- | :---: |
| **Biometric Security** | Haar Cascades Face Detection | [`services/face_service.py`](services/face_service.py) | [`tests/test_stage3_face_recognition.py`](tests/test_stage3_face_recognition.py) | ✓ 100% |
| **Biometric Security** | LBPH Facial Recognition | [`face_atm/face_recognizer.py`](face_atm/face_recognizer.py) | [`tests/test_stage3_face_recognition.py`](tests/test_stage3_face_recognition.py) | ✓ 100% |
| **Biometric Security** | Anti-Spoofing & Liveness | [`face_atm/anti_spoofing.py`](face_atm/anti_spoofing.py) | [`tests/test_anti_spoofing.py`](tests/test_anti_spoofing.py) | ✓ 100% |
| **Biometric Security** | PBKDF2 PIN Cryptography & Lockout | [`services/auth_service.py`](services/auth_service.py) | [`tests/test_stage4_atm_simulation.py`](tests/test_stage4_atm_simulation.py) | ✓ 100% |
| **Biometric Security** | ATM Hardware Bill Dispenser | [`services/atm_service.py`](services/atm_service.py) | [`tests/test_stage4_atm_simulation.py`](tests/test_stage4_atm_simulation.py) | ✓ 100% |
| **Personal Finance** | 50/30/20 Budget Formula & Vaults | [`services/finance_service.py`](services/finance_service.py) | [`tests/test_stage5_financial_assistance.py`](tests/test_stage5_financial_assistance.py) | ✓ 100% |
| **Unit IV: Language Models** | DFA Query Automaton | [`language_models/query_automaton.py`](language_models/query_automaton.py) | [`tests/test_stage6_ir_unit4.py`](tests/test_stage6_ir_unit4.py) | ✓ 100% |
| **Unit IV: Language Models** | N-gram Models & Laplace Smoothing | [`language_models/ngram_models.py`](language_models/ngram_models.py) | [`tests/test_stage6_ir_unit4.py`](tests/test_stage6_ir_unit4.py) | ✓ 100% |
| **Unit IV: Language Models** | Perplexity & Multinomial Probabilities | [`language_models/multinomial_model.py`](language_models/multinomial_model.py) | [`tests/test_stage6_ir_unit4.py`](tests/test_stage6_ir_unit4.py) | ✓ 100% |
| **Unit IV: Language Models** | Query Likelihood (Dirichlet & JM) | [`language_models/lm_ranker.py`](language_models/lm_ranker.py) | [`tests/test_stage6_ir_unit4.py`](tests/test_stage6_ir_unit4.py) | ✓ 100% |
| **Unit IV: Language Models** | Divergence From Randomness (DFR InL2)| [`language_models/dfr_ranker.py`](language_models/dfr_ranker.py) | [`tests/test_stage6_ir_unit4.py`](tests/test_stage6_ir_unit4.py) | ✓ 100% |
| **Unit IV: Language Models** | Sliding Window Passage Retrieval | [`language_models/passage_retriever.py`](language_models/passage_retriever.py) | [`tests/test_stage6_ir_unit4.py`](tests/test_stage6_ir_unit4.py) | ✓ 100% |
| **Unit IV: Language Models** | IR Evaluation Metrics (MAP, P@K, F1)| [`language_models/ir_metrics.py`](language_models/ir_metrics.py) | [`tests/test_language_models.py`](tests/test_language_models.py) | ✓ 100% |
| **Unit V: Web Retrieval** | Iterative PageRank Power Iteration | [`web_retrieval/pagerank.py`](web_retrieval/pagerank.py) | [`tests/test_stage7_ir_unit5.py`](tests/test_stage7_ir_unit5.py) | ✓ 100% |
| **Unit V: Web Retrieval** | MapReduce Inverted Indexer | [`web_retrieval/mapreduce_engine.py`](web_retrieval/mapreduce_engine.py) | [`tests/test_stage7_ir_unit5.py`](tests/test_stage7_ir_unit5.py) | ✓ 100% |
| **Unit V: Web Retrieval** | Parallel Shard Query Coordinator | [`web_retrieval/parallel_query.py`](web_retrieval/parallel_query.py) | [`tests/test_stage7_ir_unit5.py`](tests/test_stage7_ir_unit5.py) | ✓ 100% |
| **Unit V: Web Retrieval** | Polite Web Crawler & Politeness Controls| [`web_retrieval/beautifulsoup_crawler.py`](web_retrieval/beautifulsoup_crawler.py) | [`tests/test_stage7_ir_unit5.py`](tests/test_stage7_ir_unit5.py) | ✓ 100% |
| **Unit VI: IR Applications** | User Collaborative Filtering (Cosine) | [`ir_applications/collaborative_filter.py`](ir_applications/collaborative_filter.py) | [`tests/test_stage8_ir_unit6.py`](tests/test_stage8_ir_unit6.py) | ✓ 100% |
| **Unit VI: IR Applications** | Content-Based TF-IDF Recommender | [`ir_applications/content_recommender.py`](ir_applications/content_recommender.py) | [`tests/test_stage8_ir_unit6.py`](tests/test_stage8_ir_unit6.py) | ✓ 100% |
| **Unit VI: IR Applications** | Knowledge-Based Rules Engine | [`ir_applications/knowledge_recommender.py`](ir_applications/knowledge_recommender.py) | [`tests/test_stage8_ir_unit6.py`](tests/test_stage8_ir_unit6.py) | ✓ 100% |
| **Unit VI: IR Applications** | NLP NER & Subject-Predicate Triples | [`ir_applications/text_extractor.py`](ir_applications/text_extractor.py) | [`tests/test_stage8_ir_unit6.py`](tests/test_stage8_ir_unit6.py) | ✓ 100% |
| **Unit VI: IR Applications** | Vis.js RDF Semantic Knowledge Graph | [`ir_applications/knowledge_graph.py`](ir_applications/knowledge_graph.py) | [`tests/test_stage8_ir_unit6.py`](tests/test_stage8_ir_unit6.py) | ✓ 100% |
| **Hybrid IR Engine** | Multi-Model Score Fusion Search | [`services/retrieval_service.py`](services/retrieval_service.py) | [`tests/test_stage9_hybrid_search.py`](tests/test_stage9_hybrid_search.py) | ✓ 100% |
| **Administration** | SOC User Management & Audit Inspector| [`routes/admin_routes.py`](routes/admin_routes.py) | [`tests/test_stage10_admin_security.py`](tests/test_stage10_admin_security.py) | ✓ 100% |
| **Full Integration** | End-to-End System Integration Suite | [`tests/test_stage11_full_integration.py`](tests/test_stage11_full_integration.py) | [`tests/test_stage11_full_integration.py`](tests/test_stage11_full_integration.py) | ✓ 100% |

---

## 8. Troubleshooting & FAQ

### Q1: The server won't start because port 5000 is in use.
* **Fix**: Terminate any lingering Python processes using PowerShell:
  ```powershell
  Stop-Process -Name python -Force -ErrorAction SilentlyContinue
  ```
  Or change the port in `app.py` / run on port 5001:
  ```powershell
  python -c "from app import create_app; create_app().run(port=5001, debug=True)"
  ```

### Q2: My webcam is not detected or permission is denied.
* **Fix**: Ensure your browser allows camera access for `http://localhost:5000`. If you do not have a physical webcam attached, you can click the **1-Click Demo Login** or **Simulate Face Recognition** buttons on the verification page to test complete biometric verification without camera hardware.

### Q3: How do I reset the database to fresh factory state?
* **Fix**: Simply delete `data/atm_system.db` and re-run the seed script:
  ```powershell
  Remove-Item -Path data\atm_system.db -Force
  python database/seed_demo_data.py
  ```

---

## 9. Permanent Backup Safeguard Notice

* A complete, verified, byte-for-byte external backup of this project exists permanently at:  
  `B:\SY_Projects\AI_Face_ATM_IR_System_BACKUP_20261014_002019`
* This backup will **never be deleted or altered**, ensuring total protection and safety of all historical files and data.
