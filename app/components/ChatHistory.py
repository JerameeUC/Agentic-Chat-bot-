# app/components/ChatHistory.py
from __future__ import annotations
from typing import List, Tuple
import gradio as gr

History = List[Tuple[str, str]]  # [("user","hi"), ("bot","hello")]

def to_chatbot_pairs(history: History) -> list[tuple[str, str]]:
    """
    Convert [('user','..'),('bot','..')] into gr.Chatbot expected pairs.
    Pairs are [(user_text, bot_text), ...].
    """
    pairs: list[tuple[str, str]] = []
    buf_user: str | None = None
    for who, text in history:
        if who == "user":
            buf_user = text
        elif who == "bot":
            pairs.append((buf_user or "", text))
            buf_user = None
    return pairs

def build_chat_history(label: str = "Conversation") -> gr.Chatbot:
    """
    Create a Chatbot component (the large chat pane).
    Use .update(value=to_chatbot_pairs(history)) to refresh.
    """
    return gr.Chatbot(label=label, height=360, show_copy_button=True)
