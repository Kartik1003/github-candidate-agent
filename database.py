import sqlite3, os

DB_FILE = os.path.join(os.path.dirname(__file__), "candidates.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_profiles (
            login       TEXT PRIMARY KEY,
            processed_at TEXT DEFAULT (datetime('now')),
            score       REAL,
            domain      TEXT
        )
    """)
    conn.commit()
    conn.close()

def mark_processed(login: str, score: float, domain: str):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT OR REPLACE INTO processed_profiles (login, score, domain) VALUES (?, ?, ?)",
        (login, score, domain)
    )
    conn.commit()
    conn.close()

def was_processed_recently(login: str, days: int = 30) -> bool:
    """Returns True if this profile was analyzed within the last N days."""
    conn = sqlite3.connect(DB_FILE)
    row = conn.execute(
        """SELECT login FROM processed_profiles
           WHERE login = ?
           AND processed_at >= datetime('now', ?)""",
        (login, f"-{days} days")
    ).fetchone()
    conn.close()
    return row is not None

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    total = conn.execute("SELECT COUNT(*) FROM processed_profiles").fetchone()[0]
    conn.close()
    return {"total_ever_processed": total}