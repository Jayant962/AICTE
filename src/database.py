"""SQLite persistence. Stores extracted metadata + a truncated text excerpt only
(not the original file). Default path: data/docusense.db (git-ignored)."""
import json
import os
import sqlite3
from datetime import datetime, timezone

DEFAULT_DB = os.path.join("data", "docusense.db")
EXCERPT_CHARS = 1500

SCHEMA = """
CREATE TABLE IF NOT EXISTS invoices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  file_hash TEXT UNIQUE,
  file_name TEXT, source TEXT NOT NULL DEFAULT 'upload',
  vendor TEXT, invoice_number TEXT, invoice_date TEXT, due_date TEXT,
  subtotal REAL, tax REAL, total REAL, currency TEXT,
  text_excerpt TEXT, completeness REAL, user_corrected INTEGER DEFAULT 0,
  validation_status TEXT, validation_json TEXT, duplicate_json TEXT,
  anomaly_json TEXT, screening_category TEXT, indicators_json TEXT,
  created_at TEXT NOT NULL
);
"""
_NUMERIC = ("subtotal", "tax", "total")
_TEXT = ("vendor", "invoice_number", "invoice_date", "due_date", "currency", "file_name")


def connect(path=DEFAULT_DB):
    if path != ":memory:":
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def validate_for_storage(rec: dict):
    for k in _NUMERIC:
        v = rec.get(k)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float))):
            raise ValueError(f"'{k}' must be numeric or None.")
    for k in _TEXT:
        v = rec.get(k)
        if v is not None and not isinstance(v, str):
            raise ValueError(f"'{k}' must be text or None.")
        if isinstance(v, str) and len(v) > 300:
            raise ValueError(f"'{k}' is too long.")
    if not rec.get("file_hash"):
        raise ValueError("file_hash is required to avoid accidental duplicates.")


def insert_record(conn, rec: dict):
    """Insert a record. Returns new id, or None if file_hash already stored (nothing overwritten)."""
    validate_for_storage(rec)
    if conn.execute("SELECT 1 FROM invoices WHERE file_hash=?", (rec["file_hash"],)).fetchone():
        return None
    cur = conn.execute(
        """INSERT INTO invoices (file_hash,file_name,source,vendor,invoice_number,invoice_date,due_date,
        subtotal,tax,total,currency,text_excerpt,completeness,user_corrected,validation_status,
        validation_json,duplicate_json,anomaly_json,screening_category,indicators_json,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (rec["file_hash"], rec.get("file_name"), rec.get("source", "upload"), rec.get("vendor"),
         rec.get("invoice_number"), rec.get("invoice_date"), rec.get("due_date"), rec.get("subtotal"),
         rec.get("tax"), rec.get("total"), rec.get("currency"),
         (rec.get("text_excerpt") or "")[:EXCERPT_CHARS], rec.get("completeness"),
         int(bool(rec.get("user_corrected"))), rec.get("validation_status"),
         json.dumps(rec.get("validation", [])), json.dumps(rec.get("duplicates", []), default=str),
         json.dumps(rec.get("anomaly", {})), rec.get("screening_category"),
         json.dumps(rec.get("indicators", [])), datetime.now(timezone.utc).isoformat()))
    conn.commit()
    return cur.lastrowid


def fetch_all(conn) -> list:
    return [dict(r) for r in conn.execute("SELECT * FROM invoices ORDER BY id")]


def count(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]


def reset_db(conn):
    """Delete ALL stored records (demo reset)."""
    conn.execute("DELETE FROM invoices")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='invoices'")
    conn.commit()


def delete_source(conn, source: str):
    conn.execute("DELETE FROM invoices WHERE source=?", (source,))
    conn.commit()
