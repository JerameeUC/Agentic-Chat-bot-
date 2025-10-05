# /anon_bot/handler.py
"""
Stateless(ish) turn handler for the anonymous chatbot.

- `reply(user_text, history=None)` -> {"reply": str, "meta": {...}}
- `handle_turn(message, history, user)` -> History[(speaker, text)]
- `handle_text(message, history=None)` -> str  (one-shot convenience)

By default (ENABLE_LLM=0) this is fully offline/deterministic and test-friendly.
If ENABLE_LLM=1 and AI_PROVIDER=hf with proper HF env vars, it will call the
HF Inference API (or a local pipeline if available via importlib).
"""

from __future__ import annotations
import os
from typing import List, Tuple, Dict, Any

# Your existing rules module (kept)
from . import rules

# Unified providers (compliance-safe, lazy)
try:
    from agenticcore.providers_unified import generate_text, analyze_sentiment_unified, get_chat_backend
except Exception:
    # soft fallbacks
    def generate_text(prompt: str, max_tokens: int = 128) -> Dict[str, Any]:
        return {"provider": "offline", "text": f"(offline) {prompt[:160]}"}
    def analyze_sentiment_unified(text: str) -> Dict[str, Any]:
        t = (text or "").lower()
        if any(w in t for w in ["love","great","awesome","amazing","good","thanks"]): return {"provider":"heuristic","label":"positive","score":0.9}
        if any(w in t for w in ["hate","awful","terrible","bad","angry","sad"]):      return {"provider":"heuristic","label":"negative","score":0.9}
        return {"provider":"heuristic","label":"neutral","score":0.5}
    class _Stub:
        def generate(self, prompt, history=None, **kw): return "Noted. If you need help, type 'help'."
    def get_chat_backend(): return _Stub()

History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]

def _offline_reply(user_text: str) -> str:
    t = (user_text or "").strip().lower()
    if t in {"help", "/help"}:
        return "I can answer quick questions, echo text, or summarize short passages."
    if t.startswith("echo "):
        return (user_text or "")[5:]
    return "Noted. If you need help, type 'help'."

def reply(user_text: str, history: History | None = None) -> Dict[str, Any]:
    """
    Small helper used by plain JSON endpoints: returns reply + sentiment meta.
    """
    history = history or []
    if os.getenv("ENABLE_LLM", "0") == "1":
        res = generate_text(user_text, max_tokens=180)
        text = (res.get("text") or _offline_reply(user_text)).strip()
    else:
        text = _offline_reply(user_text)

    sent = analyze_sentiment_unified(user_text)
    return {"reply": text, "meta": {"sentiment": sent}}

def _coerce_history(h: Any) -> History:
    if not h:
        return []
    out: History = []
    for item in h:
        try:
            who, text = item[0], item[1]
        except Exception:
            continue
        out.append((str(who), str(text)))
    return out

def handle_turn(message: str, history: History | None, user: dict | None) -> History:
    """
    Keeps the original signature used by tests: returns updated History.
    Uses your rule-based reply for deterministic behavior.
    """
    hist = _coerce_history(history)
    user_text = (message or "").strip()
    if user_text:
        hist.append(("user", user_text))
    rep = rules.reply_for(user_text, hist)
    hist.append(("bot", rep.text))
    return hist

def handle_text(message: str, history: History | None = None) -> str:
    new_hist = handle_turn(message, history, user=None)
    return new_hist[-1][1] if new_hist else ""
