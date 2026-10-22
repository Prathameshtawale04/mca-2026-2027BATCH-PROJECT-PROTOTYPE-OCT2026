"""Database Manager for SQLite with strict transactions and foreign key enforcement."""

import sqlite3
import os
from pathlib import Path
from contextlib import contextmanager
from flask import g, current_app

def get_db_path():
    """Retrieve configured database path from Flask config or default."""
    try:
        return current_app.config.get("DATABASE_PATH")
    except RuntimeError:
        # Outside Flask application context
        base_dir = Path(__file__).resolve().parent.parent
        return base_dir / "data" / "atm_system.db"

_standalone_conn = None

def get_db():
    """Get active SQLite connection for current request or standalone context."""
    global _standalone_conn
    try:
        if "db" not in g:
            db_path = get_db_path()
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            g.db = sqlite3.connect(
                str(db_path),
                timeout=15.0
            )
            g.db.row_factory = sqlite3.Row
            # Enforce foreign key constraints
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db
    except RuntimeError:
        # Outside Flask application context (CLI scripts, migrations, tests)
        if _standalone_conn is None:
            db_path = get_db_path()
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
            _standalone_conn = sqlite3.connect(
                str(db_path),
                timeout=15.0
            )
            _standalone_conn.row_factory = sqlite3.Row
            _standalone_conn.execute("PRAGMA foreign_keys = ON;")
        return _standalone_conn

def close_db(e=None):
    """Close the current SQLite connection if open."""
    global _standalone_conn
    try:
        db = g.pop("db", None)
        if db is not None:
            db.close()
    except RuntimeError:
        if _standalone_conn is not None:
            _standalone_conn.close()
            _standalone_conn = None

def init_db(app=None):
    """Execute schema.sql to initialize all tables."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    if app is not None:
        with app.app_context():
            db = get_db()
            db.executescript(schema_sql)
            db.commit()
    else:
        db_path = get_db_path()
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()

def query_db(query, args=(), one=False):
    """Execute a parameterized SELECT query safely."""
    db = get_db()
    cursor = db.execute(query, args)
    rows = cursor.fetchall()
    cursor.close()
    if one:
        return rows[0] if rows else None
    return rows

def execute_db(query, args=(), commit=True):
    """Execute a parameterized INSERT, UPDATE, or DELETE query."""
    db = get_db()
    cursor = db.execute(query, args)
    if commit:
        db.commit()
    last_id = cursor.lastrowid
    row_count = cursor.rowcount
    cursor.close()
    return {"lastrowid": last_id, "rowcount": row_count}

@contextmanager
def db_transaction():
    """Context manager for ACID transaction rollback on failure."""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

# Convenience & compatibility aliases
transaction = db_transaction
query_all = query_db
execute_sql = execute_db

def query_one(query, args=()):
    """Execute a parameterized SELECT query and return a single row."""
    return query_db(query, args, one=True)
