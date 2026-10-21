# Database Schema & Entity Relationship Specification

The system uses an ACID-compliant SQLite relational database (`database/atm_ir.db`) with active foreign key cascade constraints.

## Relational Tables

### 1. `users`
* `account_number` (VARCHAR(20), PRIMARY KEY): Unique account ID (e.g. `ACC1001`).
* `full_name` (VARCHAR(100)): Cardholder legal name.
* `email` (VARCHAR(120), UNIQUE): Account notification email.
* `pin_hash` (VARCHAR(64)): 100,000-iteration PBKDF2 HMAC-SHA256 hex digest.
* `pin_salt` (VARCHAR(32)): 16-byte cryptographically random hex salt.
* `failed_attempts` (INTEGER): Counter for consecutive invalid PIN attempts (reset upon success).
* `is_locked` (INTEGER): Lockout boolean flag (`0` or `1`).
* `locked_until` (TIMESTAMP): Expiration timestamp for temporary lockout (15 minutes).
* `created_at` (TIMESTAMP): Account registration timestamp.

### 2. `accounts`
* `account_number` (VARCHAR(20), PK, FK -> `users.account_number` ON DELETE CASCADE).
* `balance` (DECIMAL(12, 2)): Ledger balance.
* `account_type` (VARCHAR(30)): Savings, Checking, or Admin.
* `daily_limit` (DECIMAL(10, 2)): Maximum daily withdrawal limit (default \$5,000.00).
* `updated_at` (TIMESTAMP): Balance modification timestamp.

### 3. `transactions`
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT).
* `account_number` (VARCHAR(20), FK -> `users.account_number`).
* `type` (VARCHAR(15) CHECK IN ('DEPOSIT', 'WITHDRAWAL', 'TRANSFER')).
* `amount` (DECIMAL(10, 2)): Transaction amount.
* `balance_after` (DECIMAL(12, 2)): Snapshot of balance after transaction.
* `description` (TEXT): Audit explanation.
* `timestamp` (TIMESTAMP): Operation timestamp.

### 4. `face_models`
* `account_number` (VARCHAR(20), PK, FK -> `users.account_number`).
* `model_path` (TEXT): Absolute path to serialized LBPH XML/YAML model.
* `sample_count` (INTEGER): Number of face training crops.
* `confidence_threshold` (FLOAT): Verification threshold (default 70.0).
* `trained_at` (TIMESTAMP): Last model training timestamp.

### 5. `documents`
* `doc_id` (INTEGER PRIMARY KEY AUTOINCREMENT).
* `title` (TEXT NOT NULL).
* `category` (VARCHAR(50)).
* `content` (TEXT NOT NULL).
* `author` (VARCHAR(100)).
* `created_at` (TIMESTAMP).

### 6. `knowledge_triples`
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT).
* `subject` (VARCHAR(100) NOT NULL).
* `predicate` (VARCHAR(50) NOT NULL).
* `object` (VARCHAR(100) NOT NULL).
* `confidence` (FLOAT DEFAULT 1.0).
* `source_doc_id` (INTEGER, FK -> `documents.doc_id`).

### 7. `user_interactions`
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT).
* `account_number` (VARCHAR(20)).
* `doc_id` (INTEGER, FK -> `documents.doc_id`).
* `rating` (FLOAT CHECK 1.0 TO 5.0).
* `timestamp` (TIMESTAMP).
