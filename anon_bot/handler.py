# anon_bot/handler.py
"""
Stateless(ish) turn handler for the anonymous chatbot.
Signature kept tiny: handle_turn(message, history, user) -> new_history
- message: str (user text)
- history: list of [speaker, text] or None
- user: dict-like info (ignored here, but accepted for compatibility)
"""

from __future__ import annotations
from typing import List, Tuple, Any
from . import rules

History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]

def _coerce_history(h: Any) -> History:
    if not h:
        return []
    # normalize to tuple pairs
    out: History = []
    for item in h:
        try:
            who, text = item[0], item[1]
        except Exception:
            continue
        out.append((str(who), str(text)))
    return out

def handle_turn(message: str, history: History | None, user: dict | None) -> History:
    hist = _coerce_history(history)
    user_text = (message or "").strip()
    if user_text:
        hist.append(("user", user_text))
    rep = rules.reply_for(user_text, hist)
    hist.append(("bot", rep.text))
    return hist

# Convenience: one-shot string→string (used by plain JSON endpoints)
def handle_text(message: str, history: History | None = None) -> str:
    new_hist = handle_turn(message, history, user=None)
    # last item is bot reply
    return new_hist[-1][1] if new_hist else ""
