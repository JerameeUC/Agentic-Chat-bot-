# /app/components/Card.py
import gradio as gr
from html import escape

def render_card(title: str, body_html: str | None = None, body_text: str | None = None) -> gr.HTML:
    """
    Generic panel card. Pass raw HTML (sanitized upstream) or plain text.
    """
    if body_html is None:
        body_html = f"<div style='white-space:pre-wrap'>{escape(body_text or '')}</div>"
    t = escape(title or "")
    html = f"""
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:12px 14px;background:#fff">
      <div style="font-weight:600;margin-bottom:6px;color:#0f172a">{t}</div>
      <div style="color:#334155;font-size:14px;line-height:1.5">{body_html}</div>
    </div>
    """
    return gr.HTML(value=html)
