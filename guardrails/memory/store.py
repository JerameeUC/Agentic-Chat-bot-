# /memory/sessions.py
"""
Simple in-memory session manager for chatbot history.
Supports TTL, max history, and JSON persistence.
"""

from __future__ import annotations
import time, json, uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any

History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]


@dataclass
class Session:
    session_id: str
    user_id: Optional[str] = None
    history: History = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class SessionStore:
    def __init__(self, ttl_seconds: Optional[int] = 3600, max_history: Optional[int] = 50):
        self.ttl_seconds = ttl_seconds
        self.max_history = max_history
        self._sessions: Dict[str, Session] = {}

    # --- internals ---
    def _expired(self, sess: Session) -> bool:
        if self.ttl_seconds is None:
            return False
        return (time.time() - sess.updated_at) > self.ttl_seconds

    # --- CRUD ---
    def create(self, user_id: Optional[str] = None) -> Session:
        sid = str(uuid.uuid4())
        sess = Session(session_id=sid, user_id=user_id)
        self._sessions[sid] = sess
        return sess

    def get(self, sid: str) -> Optional[Session]:
        return self._sessions.get(sid)

    def get_history(self, sid: str) -> History:
        sess = self.get(sid)
        return list(sess.history) if sess else []

    def append_user(self, sid: str, text: str) -> None:
        self._append(sid, "user", text)

    def append_bot(self, sid: str, text: str) -> None:
        self._append(sid, "bot", text)

    def _append(self, sid: str, who: str, text: str) -> None:
        sess = self.get(sid)
        if not sess:
            return
        sess.history.append((who, text))
        if self.max_history and len(sess.history) > self.max_history:
            sess.history = sess.history[-self.max_history:]
        sess.updated_at = time.time()

    # --- Data store ---
    def set(self, sid: str, key: str, value: Any) -> None:
        sess = self.get(sid)
        if sess:
            sess.data[key] = value
            sess.updated_at = time.time()

    def get_value(self, sid: str, key: str, default=None) -> Any:
        sess = self.get(sid)
        return sess.data.get(key, default) if sess else default

    def data_dict(self, sid: str) -> Dict[str, Any]:
        sess = self.get(sid)
        return dict(sess.data) if sess else {}

    # --- TTL management ---
    def sweep(self) -> int:
        """Remove expired sessions; return count removed."""
        expired = [sid for sid, s in self._sessions.items() if self._expired(s)]
        for sid in expired:
            self._sessions.pop(sid, None)
        return len(expired)

    def all_ids(self):
        return list(self._sessions.keys())

    # --- persistence ---
    def save(self, path: Path) -> None:
        payload = {
            sid: {
                "user_id": s.user_id,
                "history": s.history,
                "data": s.data,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            }
            for sid, s in self._sessions.items()
        }
        path.write_text(json.dumps(payload, indent=2))

    @classmethod
    def load(cls, path: Path) -> "SessionStore":
        store = cls()
        if not path.exists():
            return store
        raw = json.loads(path.read_text())
        for sid, d in raw.items():
            s = Session(
                session_id=sid,
                user_id=d.get("user_id"),
                history=d.get("history", []),
                data=d.get("data", {}),
                created_at=d.get("created_at", time.time()),
                updated_at=d.get("updated_at", time.time()),
            )
            store._sessions[sid] = s
        return store


# --- Module-level singleton for convenience ---
_store = SessionStore()

def new_session(user_id: Optional[str] = None) -> Session:
    return _store.create(user_id)

def history(sid: str) -> History:
    return _store.get_history(sid)

def append_user(sid: str, text: str) -> None:
    _store.append_user(sid, text)

def append_bot(sid: str, text: str) -> None:
    _store.append_bot(sid, text)

def set_value(sid: str, key: str, value: Any) -> None:
    _store.set(sid, key, value)

def get_value(sid: str, key: str, default=None) -> Any:
    return _store.get_value(sid, key, default)
