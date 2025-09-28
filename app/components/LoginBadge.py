# app/components/LoginBadge.py
import gradio as gr

def render_login_badge(is_logged_in: bool = False) -> gr.HTML:
    label = "Logged in" if is_logged_in else "Anonymous"
    color = "#2563eb" if is_logged_in else "#0ea5e9"
    html = f"""
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border:1px solid #e2e8f0;border-radius:999px;">
      <span style="width:8px;height:8px;background:{color};border-radius:999px;display:inline-block;"></span>
      <span style="color:#0f172a;font-size:13px;">{label}</span>
    </span>
    """
    return gr.HTML(value=html)
