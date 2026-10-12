"""Modified for DeskPilot AI: audit events with opt-in raw questions."""

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


def init_db() -> None:
    Path(settings.audit_db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(settings.audit_db_path) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS support_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            request_id TEXT NOT NULL,
            question_hash TEXT NOT NULL,
            question TEXT,
            source_used TEXT NOT NULL,
            trace_json TEXT NOT NULL,
            latency_ms INTEGER NOT NULL,
            retry_count INTEGER NOT NULL
        )""")


def write_audit(
    question: str,
    source_used: str,
    trace: list[str],
    *,
    request_id: str,
    latency_ms: int,
    retry_count: int,
) -> None:
    safe_trace = [
        "Query rewrite performed" if step.startswith("Query rewrite") else step for step in trace
    ]
    with sqlite3.connect(settings.audit_db_path, timeout=10) as con:
        con.execute(
            """INSERT INTO support_events
                    (created_at, request_id, question_hash, question, source_used, trace_json, latency_ms, retry_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                request_id,
                hashlib.sha256(question.encode()).hexdigest(),
                question if settings.audit_store_questions else None,
                source_used,
                json.dumps(safe_trace),
                latency_ms,
                retry_count,
            ),
        )
