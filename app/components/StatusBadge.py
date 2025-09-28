# app/components/StatusBadge.py
import gradio as gr

def render_status_badge(status: str = "online") -> gr.HTML:
    s = (status or "offline").lower()
    color = "#16a34a" if s == "online" else "#ea580c" if s == "busy" else "#ef4444"
    html = f"""
    <span style="display:inline-flex;align-items:center;gap:8px;padding:6px 10px;border:1px solid #e2e8f0;border-radius:999px;">
      <span style="width:8px;height:8px;background:{color};border-radius:999px;display:inline-block;"></span>
      <span style="color:#0f172a;font-size:13px;">{s.capitalize()}</span>
    </span>
    """
    return gr.HTML(value=html)
