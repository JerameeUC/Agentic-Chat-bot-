# /nlu/router.py
"""
Lightweight NLU router.

- Uses nlu.pipeline.analyze() to classify the user's intent.
- Maps intents to high-level actions (GREETING, HELP, FAQ, ECHO, SUMMARIZE, GENERAL, GOODBYE).
- Provides:
    route(text, ctx=None)  -> dict with intent, action, handler, params
    respond(text, history) -> quick deterministic reply for smoke tests
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

from .pipeline import analyze
from .prompts import get_system_prompt, get_few_shots

History = List[Tuple[str, str]]  # [("user","..."), ("bot","...")]

# -----------------------------
# Action / Route schema
# -----------------------------

@dataclass(frozen=True)
class Route:
    intent: str
    action: str
    handler: str                 # suggested dotted path or logical name
    params: Dict[str, Any]       # arbitrary params (e.g., {"mode":"faq"})
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Intent -> (Action, Suggested Handler, Default Params)
_ACTION_TABLE: Dict[str, Tuple[str, str, Dict[str, Any]]] = {
    "greeting": ("GREETING",  "builtin.respond", {"mode": "base"}),
    "goodbye":  ("GOODBYE",   "builtin.respond", {"mode": "base"}),
    "help":     ("HELP",      "builtin.respond", {"mode": "support"}),
    "faq":      ("FAQ",       "builtin.respond", {"mode": "faq"}),
    # Sentiment intents come from pipeline; treat as GENERAL but note tag:
    "sentiment_positive": ("GENERAL", "builtin.respond", {"mode": "base", "tag": "positive"}),
    "sentiment_negative": ("GENERAL", "builtin.respond", {"mode": "base", "tag": "negative"}),
    # Default:
    "general":  ("GENERAL",   "builtin.respond", {"mode": "base"}),
}

_DEFAULT_ACTION = ("GENERAL", "builtin.respond", {"mode": "base"})


# -----------------------------
# Routing
# -----------------------------
def route(text: str, ctx=None) -> Dict[str, Any]:
    nlu = analyze(text or "")
    intent = nlu.get("intent", "general")
    confidence = float(nlu.get("confidence", 0.0))
    action, handler, params = _ACTION_TABLE.get(intent, _DEFAULT_ACTION)

    # Simple keyword-based sentiment override
    t = (text or "").lower()
    if any(w in t for w in ["love", "great", "awesome", "amazing"]):
        intent = "sentiment_positive"
        action, handler, params = _ACTION_TABLE[intent]  # <- re-derive
    elif any(w in t for w in ["hate", "awful", "terrible", "bad"]):
        intent = "sentiment_negative"
        action, handler, params = _ACTION_TABLE[intent]  # <- re-derive

    # pass-through entities as params for downstream handlers
    entities = nlu.get("entities") or []
    if entities:
        params = {**params, "entities": entities}

    # include minimal context (optional)
    if ctx:
        params = {**params, "_ctx": ctx}

    return Route(
        intent=intent,
        action=action,
        handler=handler,
        params=params,
        confidence=confidence,
    ).to_dict()


# -----------------------------
# Built-in deterministic responder (for smoke tests)
# -----------------------------
def respond(text: str, history: Optional[History] = None) -> str:
    """
    Produce a tiny, deterministic response using system/few-shot text.
    This is only for local testing; replace with real handlers later.
    """
    r = route(text)
    intent = r["intent"]
    action = r["action"]

    # Ensure the positive case uses the exact phrasing tests expect
    if intent == "sentiment_positive":
        return "I’m glad to hear that!"

    # Choose a system flavor (not used to prompt a model here, just to keep tone)
    _ = get_system_prompt("support" if action == "HELP" else ("faq" if action == "FAQ" else "base"))
    _ = get_few_shots(intent)

    if action == "GREETING":
        return "Hi! How can I help you today?"
    if action == "GOODBYE":
        return "Goodbye! Have a great day."
    if action == "HELP":
        return "I can answer quick questions, echo text, or summarize short passages. What do you need help with?"
    if action == "FAQ":
        return "Ask a specific question (e.g., 'What is RAG?'), and I’ll answer briefly."

    # GENERAL:
    tag = r["params"].get("tag")
    if tag == "negative":
        prefix = "Sorry to hear that. "
    else:
        prefix = ""
    return prefix + "Noted. If you need help, type 'help'."
