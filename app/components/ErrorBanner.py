# /app/components/ErrorBanner.py
import gradio as gr
from html import escape

def build_error_banner() -> gr.HTML:
    return gr.HTML(visible=False)

def set_error(component: gr.HTML, message: str | None):
    """
    Helper to update an error banner in event handlers.
    Usage: error.update(**set_error(error, "Oops"))
    """
    if not message:
        return {"value": "", "visible": False}
    value = f"""
    <div style="background:#fef2f2;color:#991b1b;border:1px solid #fecaca;padding:10px 12px;border-radius:10px;">
      <strong>Error:</strong> {escape(message)}
    </div>
    """
    return {"value": value, "visible": True}
