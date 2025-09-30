# /app/components/Footer.py
import gradio as gr
from html import escape

def build_footer(version: str = "0.1.0") -> gr.HTML:
    """
    Render a simple footer with version info.
    Appears at the bottom of the Gradio Blocks UI.
    """
    ver = escape(version or "")
    html = f"""
    <div style="margin-top:24px;text-align:center;
                font-size:12px;color:#6b7280;">
      <hr style="margin:16px 0;border:none;border-top:1px solid #e5e7eb"/>
      <div>AgenticCore Chatbot — v{ver}</div>
      <div style="margin-top:4px;">
        Built with <span style="color:#ef4444;">♥</span> using Gradio
      </div>
    </div>
    """
    return gr.HTML(value=html)
