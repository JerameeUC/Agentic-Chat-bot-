# app/components/Header.py
import gradio as gr
from html import escape

def build_header(title: str = "Storefront Chatbot", subtitle: str = "Anonymous mode ready"):
    t = escape(title)
    s = escape(subtitle)
    html = f"""
    <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 4px 4px;">
      <div>
        <div style="font-weight:700;font-size:20px;color:#0f172a;">{t}</div>
        <div style="font-size:13px;color:#64748b;">{s}</div>
      </div>
    </div>
    """
    return gr.HTML(value=html)
