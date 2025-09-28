# /nlu/router.py
"""
Lightweight NLU router.

- Uses nlu.pipeline.analyze() to classify the user's intent.
- Maps intents to high-level actions (GREETING, HELP, FAQ, ECHO, SUMMARIZE, GENERAL, GOODBYE).
- Provides:
    route(text, ctx=None)  -> dict with intent, action, handler, params
    respond(text, history) -> quick deterministic reply for smoke tests

This file deliberately avoids external dependencies so it works in anonymous mode.
Later, you can swap 'handler' targets to real modules (e.g., anon_bot, logged_in_bot).
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

def route(text: str, ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Decide which action/handler should process the utterance.
    """
    nlu = analyze(text or "")
    intent = nlu.get("intent", "general")
    confidence = float(nlu.get("confidence", 0.0))
    action, handler, params = _ACTION_TABLE.get(intent, _DEFAULT_ACTION)

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
    mode = r["params"].get("mode", "base")

    # Choose a system flavor (not used to prompt a model here, but keeps wording consistent)
    _ = get_system_prompt("support" if action == "HELP" else ("faq" if action == "FAQ" else "base"))
    # Few-shots can inform canned replies (again: no model used, just tone)
    shots = get_few_shots(intent)

    if action == "GREETING":
        return "Hi! How can I help you today?"
    if action == "GOODBYE":
        return "Goodbye! Have a great day."
    if action == "HELP":
        return "I can answer quick questions, echo text, or summarize short passages. What do you need help with?"
    if action == "FAQ":
        # Trivial FAQ-style echo; swap with RAG later
        return "Ask a specific question (e.g., 'What is RAG?'), and I’ll answer briefly."
    # GENERAL:
    # If the pipeline flagged sentiment, acknowledge gently.
    tag = r["params"].get("tag")
    if tag == "positive":
        prefix = "Glad to hear it! "
    elif tag == "negative":
        prefix = "Sorry to hear that. "
    else:
        prefix = ""
    return prefix + "Noted. If you need help, type 'help'."

# -----------------------------
# Simple CLI smoke test
# -----------------------------

if __name__ == "__main__":
    tests = [
        "Hello there",
        "Can you help me?",
        "What is RAG in simple terms?",
        "This is awful.",
        "Bye!",
        "random input with no keywords",
    ]
    for t in tests:
        print(f"> {t}")
        print(" route:", route(t))
        print(" reply:", respond(t))
        print()
