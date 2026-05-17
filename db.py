"""
db.py — SQLite schema and helpers for the hybrid candidate pipeline.

Tables:
  candidates — stores full profile JSON, LLM scores, cached embeddings,
               and human feedback labels for the ML feedback loop.
"""

import sqlite3
import json
import os
import numpy as np
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "hybrid_candidates.db")


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _connect() -> sqlite3.Connection:
    """Return a connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ---------------------------------------------------------------------------
# Schema initialisation
# ---------------------------------------------------------------------------

def init_hybrid_db():
    """Create the candidates table if it does not exist."""
    conn = _connect()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            github_username  TEXT PRIMARY KEY,
            profile_json     TEXT,
            llm_score        REAL,
            embedding_vector BLOB,
            label            TEXT DEFAULT NULL,
            timestamp        TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_label
        ON candidates(label)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_candidates_timestamp
        ON candidates(timestamp)
    """)
    conn.commit()
    conn.close()
    print(f"[db] Hybrid DB initialised at {DB_PATH}")


# ---------------------------------------------------------------------------
# CRUD helpers
# ---------------------------------------------------------------------------

def upsert_candidate(
    username: str,
    profile: dict,
    llm_score: float | None = None,
    embedding_vector: np.ndarray | None = None,
    label: str | None = None,
):
    """Insert or update a candidate record."""
    conn = _connect()
    emb_blob = None
    if embedding_vector is not None:
        emb_blob = embedding_vector.tobytes()

    conn.execute(
        """
        INSERT INTO candidates
            (github_username, profile_json, llm_score, embedding_vector, label, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(github_username) DO UPDATE SET
            profile_json     = excluded.profile_json,
            llm_score        = COALESCE(excluded.llm_score,        llm_score),
            embedding_vector = COALESCE(excluded.embedding_vector, embedding_vector),
            label            = COALESCE(excluded.label,            label),
            timestamp        = excluded.timestamp
        """,
        (
            username,
            json.dumps(profile, default=str),
            llm_score,
            emb_blob,
            label,
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    conn.close()


def get_candidate(username: str) -> dict | None:
    """Retrieve a single candidate record as a dict."""
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM candidates WHERE github_username = ?", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return _row_to_dict(row)


def get_cached_embedding(username: str) -> np.ndarray | None:
    """Return the cached embedding vector, or None."""
    conn = _connect()
    row = conn.execute(
        "SELECT embedding_vector FROM candidates WHERE github_username = ?",
        (username,),
    ).fetchone()
    conn.close()
    if row and row["embedding_vector"]:
        return np.frombuffer(row["embedding_vector"], dtype=np.float32)
    return None


def update_label(username: str, label: str):
    """Set a human feedback label ('good' or 'bad') on a candidate."""
    assert label in ("good", "bad"), f"Invalid label: {label}"
    conn = _connect()
    conn.execute(
        "UPDATE candidates SET label = ? WHERE github_username = ?",
        (label, username),
    )
    conn.commit()
    conn.close()


def get_labeled_candidates() -> list[dict]:
    """Return all candidates that have been labeled."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM candidates WHERE label IS NOT NULL"
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_label_counts() -> dict:
    """Return counts of labeled candidates."""
    conn = _connect()
    rows = conn.execute(
        "SELECT label, COUNT(*) as cnt FROM candidates WHERE label IS NOT NULL GROUP BY label"
    ).fetchall()
    conn.close()
    return {r["label"]: r["cnt"] for r in rows}


def get_all_candidates(limit: int = 500) -> list[dict]:
    """Return the most recent candidates."""
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM candidates ORDER BY timestamp DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_dict(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a plain dict, deserialising JSON and blobs."""
    d = dict(row)
    if d.get("profile_json"):
        try:
            d["profile"] = json.loads(d["profile_json"])
        except json.JSONDecodeError:
            d["profile"] = {}
    if d.get("embedding_vector"):
        d["embedding_np"] = np.frombuffer(d["embedding_vector"], dtype=np.float32)
    return d
