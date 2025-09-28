# /logged_in_bot/tools.py
"""
Utilities for the logged-in chatbot flow.

Features
- PII redaction (optional) via guardrails.pii_redaction
- Sentiment (optional) via logged_in_bot.sentiment_azure (falls back locally)
- Tiny intent router: summarize | echo | chat
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

# Sentiment (ours): falls back to a local heuristic if Azure SDK/env missing
try:
    from .sentiment_azure import analyze_sentiment, SentimentResult  # type: ignore
except Exception:  # pragma: no cover
    analyze_sentiment = None
    SentimentResult = None  # type: ignore

# Guardrails redaction (optional)
try:
    from guardrails.pii_redaction import redact as pii_redact  # type: ignore
except Exception:  # pragma: no cover
    pii_redact = None

# core types (optional shape for JSON response)
try:
    from core.types import PlainChatResponse  # dataclass with .to_dict()
except Exception:  # pragma: no cover
    @dataclass
    class PlainChatResponse:  # lightweight fallback shape
        reply: str
        meta: Optional[Dict[str, Any]] = None

        def to_dict(self) -> Dict[str, Any]:
            return asdict(self)


History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]


# -------------------------
# Helpers
# -------------------------

_WHITESPACE_RE = re.compile(r"\s+")


def sanitize_text(text: str) -> str:
    """Basic sanitize/normalize; keep CPU-cheap & deterministic."""
    text = (text or "").strip()
    text = _WHITESPACE_RE.sub(" ", text)
    # Optionally cap extremely large payloads to protect inference/services
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
            # Fail open but safe
            return text
    return text


def intent_of(text: str) -> str:
    """Ultra-tiny intent: summarize|echo|help|chat."""
    t = text.lower().strip()
    if not t:
        return "empty"
    if t.startswith("summarize ") or t.startswith("summarise ") or " summarize " in f" {t} ":
        return "summarize"
    if t.startswith("echo "):
        return "echo"
    if t in {"help", "/help", "capabilities"}:
        return "help"
    return "chat"


def summarize_text(text: str, target_len: int = 120) -> str:
    """
    CPU-cheap pseudo-summarizer:
    - Extract first sentence; if long, truncate to target_len with ellipsis.
    Later you can swap this for a real HF model while keeping the same API.
    """
    # naive sentence boundary
    m = re.split(r"(?<=[.!?])\s+", text.strip())
    first = m[0] if m else text.strip()
    if len(first) <= target_len:
        return first
    return first[: target_len - 1].rstrip() + "…"


def capabilities() -> List[str]:
    return [
        "help",
        "echo <text>",
        "summarize <paragraph>",
        "sentiment tagging (logged-in mode)",
    ]


# -------------------------
# Main entry
# -------------------------

def handle_logged_in_turn(message: str, history: Optional[History], user: Optional[dict]) -> Dict[str, Any]:
    """
    Process one user turn in 'logged-in' mode.

    Returns a PlainChatResponse (dict) with:
      - reply: str
      - meta: { intent, sentiment: {label, score, backend}, redacted: bool }
    """
    history = history or []
    user_text_raw = message or ""
    user_text = sanitize_text(user_text_raw)
    redacted = False

    # Redact PII if available
    redacted_text = redact_text(user_text)
    redacted = (redacted_text != user_text)

    it = intent_of(redacted_text)

    # ---------- route ----------
    if it == "empty":
        reply = "Please type something. Try 'help' for options."
        meta = _meta(redacted, it, redacted_text)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "help":
        reply = "I can:\n" + "\n".join(f"- {c}" for c in capabilities())
        meta = _meta(redacted, it, redacted_text)
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "echo":
        payload = redacted_text.split(" ", 1)[1] if " " in redacted_text else ""
        reply = payload or "(nothing to echo)"
        meta = _meta(redacted, it, redacted_text)
        _attach_sentiment(meta, reply)  # sentiment on reply text
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    if it == "summarize":
        # Use everything after the keyword if present
        if redacted_text.lower().startswith("summarize "):
            payload = redacted_text.split(" ", 1)[1]
        elif redacted_text.lower().startswith("summarise "):
            payload = redacted_text.split(" ", 1)[1]
        else:
            payload = redacted_text
        reply = summarize_text(payload)
        meta = _meta(redacted, it, redacted_text)
        _attach_sentiment(meta, payload)  # sentiment on source text
        return PlainChatResponse(reply=reply, meta=meta).to_dict()

    # default: chat
    reply = _chat_fallback(redacted_text, history)
    meta = _meta(redacted, it, redacted_text)
    _attach_sentiment(meta, redacted_text)
    return PlainChatResponse(reply=reply, meta=meta).to_dict()


# -------------------------
# Internals
# -------------------------

def _chat_fallback(text: str, history: History) -> str:
    """
    Minimal deterministic fallback for general chat in logged-in mode.
    Swap this for a provider call if/when you enable one.
    """
    if "who are you" in text.lower():
        return "I'm the logged-in chatbot. I can echo, summarize, and tag sentiment."
    return "Noted! (logged-in mode). Type 'help' for options."

def _meta(redacted: bool, intent: str, redacted_text: str) -> Dict[str, Any]:
    return {
        "intent": intent,
        "redacted": redacted,
        "input_len": len(redacted_text),
    }

def _attach_sentiment(meta: Dict[str, Any], text: str) -> None:
    """Attach sentiment to meta if available; never raises."""
    try:
        if analyze_sentiment:
            res = analyze_sentiment(text)
            if hasattr(res, "__dict__"):
                meta["sentiment"] = {
                    "label": res.label,
                    "score": res.score,
                    "backend": res.backend,
                }
            else:  # unexpected object — store string
                meta["sentiment"] = {"label": str(res)}
        else:
            # no module available
            meta["sentiment"] = {"label": "neutral", "score": 0.5, "backend": "none"}
    except Exception as e:  # pragma: no cover
        meta["sentiment"] = {"error": f"{type(e).__name__}: {e}"}


__all__ = [
    "handle_logged_in_turn",
    "sanitize_text",
    "redact_text",
    "intent_of",
    "summarize_text",
    "capabilities",
]
