# state.py (your minimal version)
import sqlite3
import uuid
import datetime
from pathlib import Path


class SimpleSessionDB:
    def __init__(self):
        self.db_path = Path("~/.skunk/state.db").expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT,
                created_at REAL DEFAULT (strftime('%s', 'now')),
                ended_at REAL
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self.conn.commit()

    def get_messages(self, session_id: str):
        rows = self.conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]

    def append_message(self, session_id: str, role: str, content: str):
        self.conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, strftime('%s', 'now'))",
            (session_id, role, content),
        )
        self.conn.commit()

    def create_session(self, title: str = None) -> str:
        now = datetime.datetime.now()
        timestamp = int(now.timestamp())
        session_id = f"{now.isoformat()}-{uuid.uuid4().hex[-6:]}"
        self.conn.execute(
            "INSERT INTO sessions (id, title, created_at) VALUES (?, ?, ?)",
            (session_id, title, timestamp),
        )
        self.conn.commit()
        return session_id

    def get_session(self, session_id: str) -> dict:
        row = self.conn.execute(
            "SELECT id, title, created_at, ended_at FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        result = dict(row) if row else None
        if result:
            result["display_id"] = result["id"]
        return result

    def list_sessions(self, limit: int = 10) -> list:
        rows = self.conn.execute(
            "SELECT id, title, created_at, ended_at FROM sessions WHERE ended_at IS NULL ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        sessions = []
        for r in rows:
            d = dict(r)
            d["display_id"] = d["id"]
            sessions.append(d)
        return sessions

    def end_session(self, session_id: str):
        self.conn.execute(
            "UPDATE sessions SET ended_at = strftime('%s', 'now') WHERE id = ?",
            (session_id,),
        )
        self.conn.commit()

    def reopen_session(self, session_id: str):
        self.conn.execute(
            "UPDATE sessions SET ended_at = NULL WHERE id = ?",
            (session_id,),
        )
        self.conn.commit()

    def close(self):
        self.conn.close()
