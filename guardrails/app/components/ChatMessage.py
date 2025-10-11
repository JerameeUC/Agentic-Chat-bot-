# /app/components/ChatMessage.py
from __future__ import annotations
import gradio as gr
from html import escape

def render_message(role: str, text: str) -> gr.HTML:
    """
    Return a styled HTML bubble for a single message.
    role: "user" | "bot"
    """
    role = (role or "bot").lower()
    txt = escape(text or "")
    bg = "#eef2ff" if role == "user" else "#f1f5f9"
    align = "flex-end" if role == "user" else "flex-start"
    label = "You" if role == "user" else "Bot"
    html = f"""
    <div style="display:flex;justify-content:{align};margin:6px 0;">
      <div style="max-width: 85%; border-radius:12px; padding:10px 12px; background:{bg}; border:1px solid #e2e8f0;">
        <div style="font-size:12px; color:#64748b; margin-bottom:4px;">{label}</div>
        <div style="white-space:pre-wrap; line-height:1.45; font-size:14px; color:#0f172a;">{txt}</div>
      </div>
    </div>
    """
    return gr.HTML(value=html)
