# logged_in_bot/tools.py
"""
Utilities for the logged-in chatbot flow.

Features
- PII redaction (optional) via guardrails.pii_redaction
- Sentiment (Azure via importlib if configured; falls back to heuristic)
- Tiny intent router: help | remember | forget | list memory | summarize | echo | chat
- Session history capture via memory.sessions
- Lightweight RAG context via memory.rag.retriever (TF-IDF)
- Deterministic, dependency-light; safe to import in any environment
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
import os
import re

# -------------------------
# Optional imports (safe)
# -------------------------

# Guardrails redaction (optional)
try:  # pragma: no cover
    from guardrails.pii_redaction import redact as pii_redact  # type: ignore
except Exception:  # pragma: no cover
    pii_redact = None  # type: ignore

# Fallback PlainChatResponse if core.types is absent
try:  # pragma: no cover
    from core.types import PlainChatResponse  # dataclass with .to_dict()
except Exception:  # pragma: no cover
    @dataclass
    class PlainChatResponse:  # lightweight fallback shape
        reply: str
        meta: Optional[Dict[str, Any]] = None

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)

# Sentiment (unified; Azure if configured; otherwise heuristic)
try:
    from agenticcore.providers_unified import analyze_sentiment_unified as _sent
except Exception:
    def _sent(t: str) -> Dict[str, Any]:
        t = (t or "").lower()
        if any(w in t for w in ["love","great","awesome","good","thanks","glad","happy"]): return {"label":"positive","score":0.9,"backend":"heuristic"}
        if any(w in t for w in ["hate","terrible","awful","bad","angry","sad"]):          return {"label":"negative","score":0.9,"backend":"heuristic"}
        return {"label":"neutral","score":0.5,"backend":"heuristic"}

# Memory + RAG (pure-Python, no extra deps)
try:
    from memory.sessions import SessionStore, get_store
except Exception as e:  # pragma: no cover
    raise RuntimeError("memory.sessions is required for logged_in_bot.tools") from e

try:
    from memory.profile import Profile
except Exception as e:  # pragma: no cover
    raise RuntimeError("memory.profile is required for logged_in_bot.tools") from e

try:
    from memory.rag.indexer import DEFAULT_INDEX_PATH
    from memory.rag.retriever import retrieve, Filters
except Exception as e:  # pragma: no cover
    raise RuntimeError("memory.rag.{indexer,retriever} are required for logged_in_bot.tools") from e


History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]

# -------------------------
# Session store shim
# -------------------------

def _get_store():
    """Some versions expose SessionStore.default(); others don’t. Provide a shim."""
    try:
        if hasattr(SessionStore, "default") and callable(getattr(SessionStore, "default")):
            return SessionStore.default()
    except Exception:
        pass
    # Fallback: module-level singleton
    if not hasattr(_get_store, "_singleton"):
        _get_store._singleton = SessionStore()
    return _get_store._singleton

# -------------------------
# Helpers
# -------------------------

_WHITESPACE_RE = re.compile(r"\s+")

def sanitize_text(text: str) -> str:
    """Basic sanitize/normalize; keep CPU-cheap & deterministic."""
    text = (text or "").strip()
    text = _WHITESPACE_RE.sub(" ", text)
    max_len = int(os.getenv("MAX_INPUT_CHARS", "4000"))
    if len(text) > max_len:
        text = text[:max_len] + "…"
    return text

def redact_text(text: str) -> str:
    """Apply optional PII redaction if available; otherwise return text."""
    if pii_redact:
        try:
            return pii_redact(text)
        except Exception:
            return text
    return text

def _simple_sentiment(text: str) -> Dict[str, Any]:
    t = (text or "").lower()
    pos = any(w in t for w in ["love", "great", "awesome", "good", "thanks", "glad", "happy"])
    neg = any(w in t for w in ["hate", "terrible", "awful", "bad", "angry", "sad"])
    label = "positive" if pos and not neg else "negative" if neg and not pos else "neutral"
    score = 0.8 if label != "neutral" else 0.5
    return {"label": label, "score": score, "backend": "heuristic"}

def _sentiment_meta(text: str) -> Dict[str, Any]:
    try:
        res = _sent(text)
        # Normalize common shapes
        if isinstance(res, dict):
            label = str(res.get("label", "neutral"))
            score = float(res.get("score", 0.5))
            backend = str(res.get("backend", res.get("provider", "azure")))
            return {"label": label, "score": score, "backend": backend}
    except Exception:
        pass
    return _simple_sentiment(text)

def intent_of(text: str) -> str:
    """Tiny intent classifier."""
    t = (text or "").lower().strip()
    if not t:
        return "empty"
    if t in {"help", "/help", "capabilities"}:
        return "help"
    if t.startswith("remember ") and ":" in t:
        return "memory_remember"
    if t.startswith("forget "):
        return "memory_forget"
    if t == "list memory":
        return "memory_list"
    if t.startswith("summarize ") or t.startswith("summarise ") or " summarize " in f" {t} ":
        return "summarize"
    if t.startswith("echo "):
        return "echo"
    return "chat"

def summarize_text(text: str, target_len: int = 120) -> str:
    m = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    first = m[0] if m else (text or "").strip()
    if len(first) <= target_len:
        return first
    return first[: target_len - 1].rstrip() + "…"

def capabilities() -> List[str]:
    return [
        "help",
        "remember <key>: <value>",
        "forget <key>",
        "list memory",
        "echo <text>",
        "summarize <paragraph>",
        "sentiment tagging (logged-in mode)",
    ]

def _handle_memory_cmd(user_id: str, text: str) -> Optional[str]:
    prof = Profile.load(user_id)
    m = re.match(r"^\s*remember\s+([^:]+)\s*:\s*(.+)$", text, flags=re.I)
    if m:
        key, val = m.group(1).strip(), m.group(2).strip()
        prof.remember(key, val)
        return f"Okay, I'll remember **{key}**."
    m = re.match(r"^\s*forget\s+(.+?)\s*$", text, flags=re.I)
    if m:
        key = m.group(1).strip()
        return "Forgot." if prof.forget(key) else f"I had nothing stored as **{key}**."
    if re.match(r"^\s*list\s+memory\s*$", text, flags=re.I):
        keys = prof.list_notes()
        return "No saved memory yet." if not keys else "Saved keys: " + ", ".join(keys)
    return None

def _retrieve_context(query: str, k: int = 4) -> List[str]:
    passages = retrieve(query, k=k, index_path=DEFAULT_INDEX_PATH, filters=None)
    return [p.text for p in passages]

# -------------------------
# Main entry
# -------------------------

def handle_logged_in_turn(message: str, history: Optional[History], user: Optional[dict]) -> Dict[str, Any]:
    """
    Process one user turn in 'logged-in' mode.

    Returns a PlainChatResponse (dict) with:
      - reply: str
      - meta: { intent, sentiment: {...}, redacted: bool, input_len: int }
    """
    history = history or []
    user_text_raw = message or ""
    user_text = sanitize_text(user_text_raw)

    # Redaction (if configured)
    redacted_text = redact_text(user_text)
    redacted = (redacted_text != user_text)

    it = intent_of(redacted_text)

    # Compute sentiment once (always attach — satisfies tests)
    sentiment = _sentiment_meta(redacted_text)

    # ---------- route ----------
    if it == "empty":
        reply = "Please type something. Try 'help' for options."
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "help":
        reply = "I can:\n" + "\n".join(f"- {c}" for c in capabilities())
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it.startswith("memory_"):
        user_id = (user or {}).get("id") or "guest"
        mem_reply = _handle_memory_cmd(user_id, redacted_text)
        reply = mem_reply or "Sorry, I didn't understand that memory command."
        # track in session
        store = get_store()
        store.append_user(user_id, user_text)
        store.append_bot(user_id, reply)
        meta = _meta(redacted, "memory_cmd", redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "echo":
        payload = redacted_text.split(" ", 1)[1] if " " in redacted_text else ""
        reply = payload or "(nothing to echo)"
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "summarize":
        if redacted_text.lower().startswith("summarize "):
            payload = redacted_text.split(" ", 1)[1]
        elif redacted_text.lower().startswith("summarise "):
            payload = redacted_text.split(" ", 1)[1]
        else:
            payload = redacted_text
        reply = summarize_text(payload)
        meta = _meta(redacted, it, redacted_text, sentiment)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    # default: chat (with RAG)
    user_id = (user or {}).get("id") or "guest"
    ctx_chunks = _retrieve_context(redacted_text, k=4)
    if ctx_chunks:
        reply = "Here's what I found:\n- " + "\n- ".join(
            c[:220].replace("\n", " ") + ("…" if len(c) > 220 else "") for c in ctx_chunks
        )
    else:
        reply = "I don’t see anything relevant in your documents. Ask me to index files or try a different query."

    # session trace
    store = get_store()
    store.append_user(user_id, user_text)
    store.append_bot(user_id, reply)

    meta = _meta(redacted, it, redacted_text, sentiment)
    return PlainChatResponse(reply=reply, meta=meta).to_dict()

# -------------------------
# Internals
# -------------------------

def _meta(redacted: bool, intent: str, redacted_text: str, sentiment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "intent": intent,
        "redacted": redacted,
        "input_len": len(redacted_text),
        "sentiment": sentiment,
    }

__all__ = [
    "handle_logged_in_turn",
    "sanitize_text",
    "redact_text",
    "intent_of",
    "summarize_text",
    "capabilities",
]
