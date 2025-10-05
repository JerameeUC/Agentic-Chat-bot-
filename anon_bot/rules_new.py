import re
from typing import Optional


# Simple, deterministic rules:
def _intent_greeting(text: str) -> Optional[str]:
    if re.search(r'\b(hi|hello|hey)\b', text, re.IGNORECASE):
        return 'Hi there! I am an anonymous, rule-based helper. Ask me about hours, contact, or help.'
    return None


def _intent_help(text: str) -> Optional[str]:
    if re.search(r'\b(help|what can you do|commands)\b', text, re.IGNORECASE):
        return ("I’m a simple rule-based bot. Try:\n"
                "- 'hours' to see hours\n"
                "- 'contact' to get contact info\n"
                "- 'reverse <text>' to reverse text\n")
    return None


def _intent_hours(text: str) -> Optional[str]:
    if re.search(r'\bhours?\b', text, re.IGNORECASE):
        return 'We are open Mon-Fri, 9am-5am (local time).'
    return None


def _intent_contact(text: str) -> Optional[str]:
    if re.search(r'\b(contact|support|reach)\b', text, re.IGNORECASE):
        return 'You can reach support at our website contact form.'
    return None


def _intent_reverse(text: str) -> Optional[str]:
    s = text.strip()
    if s.lower().startswith('reverse'):
        payload = s[7:].strip()
        return payload[::-1] if payload else "There's nothing to reverse."
    return None


def _fallback(_text: str) -> str:
    return "I am not sure how to help with that. Type 'help' to see what I can do."


RULES = [
    _intent_reverse,
    _intent_greeting,
    _intent_help,
    _intent_hours,
    _intent_contact
]


def route(text: str) -> str:
    for rule in RULES:
        resp = rule(text)
        if resp is not None:
            return resp
    return _fallback(text)