import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.getenv("SMARTCARE_DB_PATH", "data/smartcare.db")

def _connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection

def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                flags_json TEXT NOT NULL
            )
        """)

def save_measurement(payload, flags):
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        cursor = conn.execute(
            "INSERT INTO measurements (created_at, payload_json, flags_json) VALUES (?, ?, ?)",
            (created_at, json.dumps(payload), json.dumps(flags))
        )
        record_id = cursor.lastrowid
    return {"id": record_id, "created_at": created_at}

def list_measurements(limit=50):
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, created_at, payload_json, flags_json FROM measurements ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [{
        "id": row["id"],
        "created_at": row["created_at"],
        "measurements": json.loads(row["payload_json"]),
        "flags": json.loads(row["flags_json"])
    } for row in rows]
