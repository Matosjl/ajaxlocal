"""Observability — structured logging of every agent action with timing + token usage."""
from __future__ import annotations
import json
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class Observer:
    """Thread-safe SQLite-backed event logger. Every tool call, LLM call, and plan step is recorded."""

    def __init__(self, db_path: str = "/app/agent_core/data/observability.db"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_schema()

    def _conn(self):
        c = sqlite3.connect(self.db_path, check_same_thread=False)
        c.row_factory = sqlite3.Row
        return c

    def _init_schema(self):
        with self._lock, self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    ts TEXT,
                    type TEXT,
                    name TEXT,
                    duration_ms INTEGER,
                    prompt_tokens INTEGER DEFAULT 0,
                    completion_tokens INTEGER DEFAULT 0,
                    payload TEXT,
                    status TEXT DEFAULT 'ok'
                );
                CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id, ts);
                CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
            """)

    def log(
        self,
        session_id: str,
        type_: str,
        name: str,
        duration_ms: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        payload: Optional[dict] = None,
        status: str = "ok",
    ) -> str:
        eid = str(uuid.uuid4())
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    eid,
                    session_id,
                    datetime.now(timezone.utc).isoformat(),
                    type_,
                    name,
                    duration_ms,
                    prompt_tokens,
                    completion_tokens,
                    json.dumps(payload or {}, default=str)[:8000],
                    status,
                ),
            )
        return eid

    def list_events(self, session_id: Optional[str] = None, limit: int = 100) -> list[dict]:
        with self._lock, self._conn() as c:
            if session_id:
                rows = c.execute(
                    "SELECT * FROM events WHERE session_id=? ORDER BY ts DESC LIMIT ?",
                    (session_id, limit),
                ).fetchall()
            else:
                rows = c.execute(
                    "SELECT * FROM events ORDER BY ts DESC LIMIT ?", (limit,)
                ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                try:
                    d["payload"] = json.loads(d["payload"])
                except Exception:
                    pass
                out.append(d)
            return out

    def stats(self, session_id: Optional[str] = None) -> dict:
        with self._lock, self._conn() as c:
            where = "WHERE session_id=?" if session_id else ""
            params = (session_id,) if session_id else ()
            row = c.execute(
                f"""
                SELECT COUNT(*) as total,
                       SUM(prompt_tokens) as p_tokens,
                       SUM(completion_tokens) as c_tokens,
                       SUM(duration_ms) as total_ms
                FROM events {where}
                """,
                params,
            ).fetchone()
            return {
                "total_events": row["total"] or 0,
                "prompt_tokens": row["p_tokens"] or 0,
                "completion_tokens": row["c_tokens"] or 0,
                "total_duration_ms": row["total_ms"] or 0,
            }


class Timer:
    """Context manager for timing operations."""
    def __enter__(self):
        self.t0 = time.time()
        return self
    def __exit__(self, *args):
        self.elapsed_ms = int((time.time() - self.t0) * 1000)
