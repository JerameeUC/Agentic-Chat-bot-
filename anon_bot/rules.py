# anon_bot/rules.py
"""
Lightweight rule set for an anonymous chatbot.
No external providers required. Pure-Python, deterministic.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

# ---- Types ----
History = List[Tuple[str, str]]  # e.g., [("user","hi"), ("bot","hello!")]

@dataclass(frozen=True)
class Reply:
    text: str
    meta: Dict[str, str] | None = None


def normalize(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def capabilities() -> List[str]:
    return [
        "help",
        "reverse <text>",
        "echo <text>",
        "small talk (hi/hello/hey)",
    ]


def intent_of(text: str) -> str:
    t = normalize(text)
    if not t:
        return "empty"
    if t in {"help", "/help", "capabilities"}:
        return "help"
    if t.startswith("reverse "):
        return "reverse"
    if t.startswith("echo "):
        return "echo"
    if t in {"hi", "hello", "hey"}:
        return "greet"
    return "chat"


def handle_help() -> Reply:
    lines = ["I can:"]
    for c in capabilities():
        lines.append(f"- {c}")
    return Reply("\n".join(lines))


def handle_reverse(t: str) -> Reply:
    payload = t.split(" ", 1)[1] if " " in t else ""
    return Reply(payload[::-1] if payload else "(nothing to reverse)")


def handle_echo(t: str) -> Reply:
    payload = t.split(" ", 1)[1] if " " in t else ""
    return Reply(payload or "(nothing to echo)")


def handle_greet() -> Reply:
    return Reply("Hello! 👋  Type 'help' to see what I can do.")


def handle_chat(t: str, history: History) -> Reply:
    # Very simple “ELIZA-ish” fallback.
    if "help" in t:
        return handle_help()
    if "you" in t and "who" in t:
        return Reply("I'm a tiny anonymous chatbot kernel.")
    return Reply("Noted. (anonymous mode)  Type 'help' for commands.")


def reply_for(text: str, history: History) -> Reply:
    it = intent_of(text)
    if it == "empty":
        return Reply("Please type something. Try 'help'.")
    if it == "help":
        return handle_help()
    if it == "reverse":
        return handle_reverse(text)
    if it == "echo":
        return handle_echo(text)
    if it == "greet":
        return handle_greet()
    return handle_chat(text.lower(), history)
