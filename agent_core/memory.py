"""Memory — conversation sessions and per-session message history (SQLite)."""
from __future__ import annotations
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class Memory:
    """Persistent multi-session memory backed by SQLite (works offline, no Mongo dependency)."""

    def __init__(self, db_path: str = "/app/agent_core/data/memory.db"):
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
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    provider TEXT,
                    model TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    state TEXT DEFAULT '{}'
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    tool_calls TEXT,
                    tool_call_id TEXT,
                    name TEXT,
                    plan TEXT,
                    created_at TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id, created_at);
            """)

    # ---- Sessions ----
    def create_session(self, title: str = "Nova conversa", provider: str = "openrouter", model: str = "openrouter/auto") -> dict:
        sid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO sessions(id,title,provider,model,created_at,updated_at,state) VALUES(?,?,?,?,?,?,?)",
                (sid, title, provider, model, now, now, "{}"),
            )
        return {"id": sid, "title": title, "provider": provider, "model": model, "created_at": now, "updated_at": now}

    def list_sessions(self) -> list[dict]:
        with self._lock, self._conn() as c:
            rows = c.execute("SELECT * FROM sessions ORDER BY updated_at DESC").fetchall()
            return [dict(r) for r in rows]

    def get_session(self, sid: str) -> Optional[dict]:
        with self._lock, self._conn() as c:
            r = c.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
            return dict(r) if r else None

    def update_session(self, sid: str, **fields):
        if not fields:
            return
        cols = ", ".join(f"{k}=?" for k in fields.keys())
        vals = list(fields.values()) + [datetime.now(timezone.utc).isoformat(), sid]
        with self._lock, self._conn() as c:
            c.execute(f"UPDATE sessions SET {cols}, updated_at=? WHERE id=?", vals)

    def delete_session(self, sid: str):
        with self._lock, self._conn() as c:
            c.execute("DELETE FROM messages WHERE session_id=?", (sid,))
            c.execute("DELETE FROM sessions WHERE id=?", (sid,))

    # ---- Messages ----
    def add_message(
        self,
        sid: str,
        role: str,
        content: str = "",
        tool_calls: Optional[list] = None,
        tool_call_id: Optional[str] = None,
        name: Optional[str] = None,
        plan: Optional[str] = None,
    ) -> dict:
        mid = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with self._lock, self._conn() as c:
            c.execute(
                "INSERT INTO messages VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    mid, sid, role, content,
                    json.dumps(tool_calls) if tool_calls else None,
                    tool_call_id, name, plan, now,
                ),
            )
            c.execute("UPDATE sessions SET updated_at=? WHERE id=?", (now, sid))
        return {"id": mid, "session_id": sid, "role": role, "content": content,
                "tool_calls": tool_calls, "tool_call_id": tool_call_id, "name": name,
                "plan": plan, "created_at": now}

    def get_messages(self, sid: str) -> list[dict]:
        with self._lock, self._conn() as c:
            rows = c.execute(
                "SELECT * FROM messages WHERE session_id=? ORDER BY created_at ASC", (sid,)
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                if d.get("tool_calls"):
                    try:
                        d["tool_calls"] = json.loads(d["tool_calls"])
                    except Exception:
                        pass
                out.append(d)
            return out

    def to_llm_messages(self, sid: str, system_prompt: str, max_messages: int = 30) -> list[dict]:
        """Convert stored messages into OpenAI-compatible message list (last N for context budget)."""
        msgs = self.get_messages(sid)[-max_messages:]
        result = [{"role": "system", "content": system_prompt}]
        for m in msgs:
            entry = {"role": m["role"]}
            if m["role"] == "assistant" and m.get("tool_calls"):
                entry["content"] = m.get("content") or None
                entry["tool_calls"] = [
                    {"id": tc["id"], "type": "function",
                     "function": {"name": tc["name"], "arguments": tc["arguments"]}}
                    for tc in m["tool_calls"]
                ]
            elif m["role"] == "tool":
                entry["content"] = m["content"] or ""
                entry["tool_call_id"] = m.get("tool_call_id") or ""
                if m.get("name"):
                    entry["name"] = m["name"]
            else:
                entry["content"] = m["content"] or ""
            result.append(entry)
        return result
