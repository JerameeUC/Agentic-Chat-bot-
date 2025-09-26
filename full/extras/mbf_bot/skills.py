# skills.py
"""
Small, dependency-free helpers used by the MBF SimpleBot.
"""

from typing import List

_CAPS: List[str] = [
    "echo-reverse",          # reverse <text>
    "help",                  # help / capabilities
    "chatbot-sentiment",     # delegate to ChatBot() if available
]

def normalize(text: str) -> str:
    """Normalize user text for lightweight command routing."""
    return (text or "").strip().lower()

def reverse_text(text: str) -> str:
    """Return the input string reversed."""
    return (text or "")[::-1]

def capabilities() -> List[str]:
    """Return a stable list of bot capabilities."""
    return list(_CAPS)

def is_empty(text: str) -> bool:
    """True if message is blank after trimming."""
    return len((text or "").strip()) == 0
