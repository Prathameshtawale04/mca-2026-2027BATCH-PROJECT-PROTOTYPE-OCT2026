-- Intelligent Face Recognition ATM Security, Financial Assistance and Information Retrieval System
-- Unified SQLite Schema Definition
-- Strict Foreign Key Enforcement & ACID Transactions

PRAGMA foreign_keys = ON;

-- 1. Users Table (Core authentication, credentials, lockout policy)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('admin', 'customer')),
    full_name TEXT NOT NULL,
    pin_hash TEXT NOT NULL,
    pin_salt TEXT NOT NULL,
    failed_login_attempts INTEGER DEFAULT 0,
    is_locked INTEGER DEFAULT 0,
    locked_until TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. ATM Accounts Table
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    account_type TEXT DEFAULT 'SAVINGS' CHECK(account_type IN ('SAVINGS', 'CHECKING')),
    balance REAL NOT NULL DEFAULT 1000.0,
    daily_limit REAL DEFAULT 5000.0,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_accounts_num ON accounts(account_number);
CREATE INDEX IF NOT EXISTS idx_accounts_user ON accounts(user_id);

-- 3. ATM Transactions Ledger (ACID banking simulation with reference numbers)
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    account_number TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER')),
    amount REAL NOT NULL,
    balance_after REAL NOT NULL,
    reference_no TEXT UNIQUE NOT NULL,
    description TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_tx_account ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_tx_ref ON transactions(reference_no);

-- 4. Biometric Face Metadata Table
CREATE TABLE IF NOT EXISTS face_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    account_number TEXT NOT NULL,
    sample_count INTEGER DEFAULT 0,
    model_path TEXT NOT NULL,
    confidence_threshold REAL DEFAULT 70.0,
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_verified_at TIMESTAMP NULL,
    status TEXT DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'INACTIVE', 'REVOKED')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_face_user ON face_metadata(user_id);

-- 5. Personal Finance Entries (Income & Expenses tracking)
CREATE TABLE IF NOT EXISTS finance_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    entry_type TEXT NOT NULL CHECK(entry_type IN ('INCOME', 'EXPENSE')),
    category TEXT NOT NULL,
    amount REAL NOT NULL,
    entry_date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_finance_user ON finance_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_finance_date ON finance_entries(entry_date);

-- 6. Monthly Budgets & 50/30/20 Smart Financial Allocation
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    month_year TEXT NOT NULL, -- Format: YYYY-MM
    total_income REAL NOT NULL DEFAULT 0.0,
    needs_budget REAL NOT NULL DEFAULT 0.0,    -- 50%
    wants_budget REAL NOT NULL DEFAULT 0.0,    -- 30%
    savings_budget REAL NOT NULL DEFAULT 0.0,  -- 20%
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, month_year),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 7. Savings Goals Table
CREATE TABLE IF NOT EXISTS savings_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    goal_name TEXT NOT NULL,
    target_amount REAL NOT NULL,
    current_amount REAL DEFAULT 0.0,
    target_date DATE,
    status TEXT DEFAULT 'IN_PROGRESS' CHECK(status IN ('IN_PROGRESS', 'COMPLETED', 'PAUSED')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_goals_user ON savings_goals(user_id);

-- 8. Academic IR Document Corpus
CREATE TABLE IF NOT EXISTS documents (
    doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    author TEXT DEFAULT 'Academic Staff',
    pagerank_score REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Passage Indexing (Unit IV Passage Retrieval)
CREATE TABLE IF NOT EXISTS passages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    passage_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_char INTEGER DEFAULT 0,
    end_char INTEGER DEFAULT 0,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_passages_doc ON passages(doc_id);

-- 10. Inverted Index Table (Unit V MapReduce / VSM)
CREATE TABLE IF NOT EXISTS inverted_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    doc_id INTEGER NOT NULL,
    term_frequency INTEGER NOT NULL,
    positions TEXT,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_inverted_term ON inverted_index(term);

-- 11. Web Crawled Pages Table (Unit V Crawler)
CREATE TABLE IF NOT EXISTS crawl_pages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT,
    content_text TEXT,
    status_code INTEGER DEFAULT 200,
    depth INTEGER DEFAULT 0,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Web Link Graph for PageRank
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url TEXT NOT NULL,
    target_url TEXT NOT NULL,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 13. Search Query History Table
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    account_number TEXT,
    query_text TEXT NOT NULL,
    search_type TEXT DEFAULT 'HYBRID',
    results_count INTEGER DEFAULT 0,
    response_time_ms REAL DEFAULT 0.0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_search_hist_user ON search_history(user_id);

-- 14. User-Item Interaction Matrix for Collaborative Filtering (Unit VI)
CREATE TABLE IF NOT EXISTS user_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    doc_id INTEGER NOT NULL,
    rating REAL NOT NULL CHECK(rating >= 1.0 AND rating <= 5.0),
    interaction_type TEXT DEFAULT 'RATING',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);

-- 15. Semantic Web Knowledge Triples (Subject-Predicate-Object) (Unit VI)
CREATE TABLE IF NOT EXISTS knowledge_triples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object TEXT NOT NULL,
    confidence REAL DEFAULT 1.0,
    source_doc_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_doc_id) REFERENCES documents(doc_id) ON DELETE SET NULL
);

-- 16. Security Audit Event Logs (Role security, PIN attempts, Lockouts, Admin events)
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    account_number TEXT,
    event_type TEXT NOT NULL,
    details TEXT,
    ip_address TEXT DEFAULT '127.0.0.1',
    status TEXT DEFAULT 'INFO' CHECK(status IN ('INFO', 'SUCCESS', 'WARNING', 'FAILURE')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id);
