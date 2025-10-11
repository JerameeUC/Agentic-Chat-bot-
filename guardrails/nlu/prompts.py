# /nlu/prompts.py
"""
Reusable prompt templates for NLU and chatbot responses.

These can be imported anywhere in the app to keep wording consistent.
They are plain strings / dicts — no external deps required.
"""

from typing import Dict

# -----------------------------
# System prompts
# -----------------------------

SYSTEM_BASE = """\
You are a helpful, polite chatbot. 
Answer briefly unless asked for detail.
"""

SYSTEM_FAQ = """\
You are a factual Q&A assistant.
Answer questions directly, citing facts when possible.
"""

SYSTEM_SUPPORT = """\
You are a friendly support assistant.
Offer clear, step-by-step help when the user asks for guidance.
"""

# -----------------------------
# Few-shot examples
# -----------------------------

FEW_SHOTS: Dict[str, list] = {
    "greeting": [
        {"user": "Hello", "bot": "Hi there! How can I help you today?"},
        {"user": "Good morning", "bot": "Good morning! What’s up?"},
    ],
    "goodbye": [
        {"user": "Bye", "bot": "Goodbye! Have a great day."},
        {"user": "See you later", "bot": "See you!"},
    ],
    "help": [
        {"user": "I need help", "bot": "Sure! What do you need help with?"},
        {"user": "Can you assist me?", "bot": "Of course, happy to assist."},
    ],
    "faq": [
        {"user": "What is RAG?", "bot": "RAG stands for Retrieval-Augmented Generation."},
        {"user": "Who created this bot?", "bot": "It was built by our project team."},
    ],
}

# -----------------------------
# Utility
# -----------------------------

def get_system_prompt(mode: str = "base") -> str:
    """
    Return a system-level prompt string.
    mode: "base" | "faq" | "support"
    """
    if mode == "faq":
        return SYSTEM_FAQ
    if mode == "support":
        return SYSTEM_SUPPORT
    return SYSTEM_BASE


def get_few_shots(intent: str) -> list:
    """
    Return few-shot examples for a given intent label.
    """
    return FEW_SHOTS.get(intent, [])


if __name__ == "__main__":
    print("System prompt:", get_system_prompt("faq"))
    print("Examples for 'greeting':", get_few_shots("greeting"))
