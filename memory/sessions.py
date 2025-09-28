# /memory/sessions.py
"""
Minimal session store for chat history + per-session data.

Features
- In-memory store with thread safety
- Create/get/update/delete sessions
- Append chat turns: ("user"| "bot", text)
- Optional TTL cleanup and max-history cap
- JSON persistence (save/load)
- Deterministic, dependency-free

Intended to interoperate with anon_bot and logged_in_bot:
  - History shape: List[Tuple[str, str]]  e.g., [("user","hi"), ("bot","hello")]
"""

from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import time
import uuid
import json
import threading

History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]

# -----------------------------
# Data model
# -----------------------------

@dataclass
class Session:
    session_id: str
    user_id: Optional[str] = None
    created_at: float = field(default_factory=lambda: time.time())
    updated_at: float = field(default_factory=lambda: time.time())
    data: Dict[str, Any] = field(default_factory=dict)     # arbitrary per-session state
    history: History = field(default_factory=list)         # chat transcripts

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # dataclasses with tuples serialize fine, ensure tuples not lost if reloaded
        return d

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Session":
        s = Session(
            session_id=d["session_id"],
            user_id=d.get("user_id"),
            created_at=float(d.get("created_at", time.time())),
            updated_at=float(d.get("updated_at", time.time())),
            data=dict(d.get("data", {})),
            history=[(str(who), str(text)) for who, text in d.get("history", [])],
        )
        return s


# -----------------------------
# Store
# -----------------------------

class SessionStore:
    """
    Thread-safe in-memory session registry with optional TTL and persistence.
    """

    def __init__(
        self,
        ttl_seconds: Optional[int] = 60 * 60,   # 1 hour default; set None to disable
        max_history: int = 200,                 # cap messages per session
    ) -> None:
        self._ttl = ttl_seconds
        self._max_history = max_history
        self._lock = threading.RLock()
        self._sessions: Dict[str, Session] = {}

    # ---- id helpers ----

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex

    # ---- CRUD ----

    def create(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> Session:
        with self._lock:
            sid = session_id or self.new_id()
            s = Session(session_id=sid, user_id=user_id)
            self._sessions[sid] = s
            return s

    def get(self, session_id: str, create_if_missing: bool = False, user_id: Optional[str] = None) -> Optional[Session]:
        with self._lock:
            s = self._sessions.get(session_id)
            if s is None and create_if_missing:
                s = self.create(user_id=user_id, session_id=session_id)
            return s

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None

    def all_ids(self) -> List[str]:
        with self._lock:
            return list(self._sessions.keys())

    # ---- housekeeping ----

    def _expired(self, s: Session) -> bool:
        if self._ttl is None:
            return False
        return (time.time() - s.updated_at) > self._ttl

    def sweep(self) -> int:
        """
        Remove expired sessions. Returns number removed.
        """
        with self._lock:
            dead = [sid for sid, s in self._sessions.items() if self._expired(s)]
            for sid in dead:
                self._sessions.pop(sid, None)
            return len(dead)

    # ---- history ops ----

    def append_user(self, session_id: str, text: str) -> Session:
        return self._append(session_id, "user", text)

    def append_bot(self, session_id: str, text: str) -> Session:
        return self._append(session_id, "bot", text)

    def _append(self, session_id: str, who: str, text: str) -> Session:
        with self._lock:
            s = self._sessions.get(session_id)
            if s is None:
                s = self.create(session_id=session_id)
            s.history.append((who, text))
            if self._max_history and len(s.history) > self._max_history:
                # Keep most recent N entries
                s.history = s.history[-self._max_history :]
            s.updated_at = time.time()
            return s

    def get_history(self, session_id: str) -> History:
        with self._lock:
            s = self._sessions.get(session_id)
            return list(s.history) if s else []

    def clear_history(self, session_id: str) -> bool:
        with self._lock:
            s = self._sessions.get(session_id)
            if not s:
                return False
            s.history.clear()
            s.updated_at = time.time()
            return True

    # ---- key/value per-session data ----

    def set(self, session_id: str, key: str, value: Any) -> Session:
        with self._lock:
            s = self._sessions.get(session_id)
            if s is None:
                s = self.create(session_id=session_id)
            s.data[key] = value
            s.updated_at = time.time()
            return s

    def get_value(self, session_id: str, key: str, default: Any = None) -> Any:
        with self._lock:
            s = self._sessions.get(session_id)
            if not s:
                return default
            return s.data.get(key, default)

    def data_dict(self, session_id: str) -> Dict[str, Any]:
        with self._lock:
            s = self._sessions.get(session_id)
            return dict(s.data) if s else {}

    # ---- persistence ----

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            payload = {
                "ttl_seconds": self._ttl,
                "max_history": self._max_history,
                "saved_at": time.time(),
                "sessions": {sid: s.to_dict() for sid, s in self._sessions.items()},
            }
        p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SessionStore":
        p = Path(path)
        if not p.is_file():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        store = cls(
            ttl_seconds=data.get("ttl_seconds"),
            max_history=int(data.get("max_history", 200)),
        )
        sessions = data.get("sessions", {})
        with store._lock:
            for sid, sd in sessions.items():
                store._sessions[sid] = Session.from_dict(sd)
        return store


# -----------------------------
# Module-level singleton (optional)
# -----------------------------

_default_store: Optional[SessionStore] = None

def get_store() -> SessionStore:
    global _default_store
    if _default_store is None:
        _default_store = SessionStore()
    return _default_store

def new_session(user_id: Optional[str] = None) -> Session:
    return get_store().create(user_id=user_id)

def append_user(session_id: str, text: str) -> Session:
    return get_store().append_user(session_id, text)

def append_bot(session_id: str, text: str) -> Session:
    return get_store().append_bot(session_id, text)

def history(session_id: str) -> History:
    return get_store().get_history(session_id)

def set_value(session_id: str, key: str, value: Any) -> Session:
    return get_store().set(session_id, key, value)

def get_value(session_id: str, key: str, default: Any = None) -> Any:
    return get_store().get_value(session_id, key, default)

def sweep() -> int:
    return get_store().sweep()
