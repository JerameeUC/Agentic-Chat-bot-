# /app/components/LoadingSpinner.py
import gradio as gr

_SPINNER = """
<div class="spinner" style="display:flex;gap:8px;align-items:center;color:#475569;">
  <svg width="18" height="18" viewBox="0 0 24 24" class="spin">
    <circle cx="12" cy="12" r="10" stroke="#94a3b8" stroke-width="3" fill="none" opacity="0.3"/>
    <path d="M22 12a10 10 0 0 1-10 10" stroke="#475569" stroke-width="3" fill="none"/>
  </svg>
  <span>Thinking…</span>
</div>
<style>
  .spin{ animation:spin 1s linear infinite;}
  @keyframes spin { from{transform:rotate(0deg);} to{transform:rotate(360deg);} }
</style>
"""

def build_spinner(visible: bool = False) -> gr.HTML:
    return gr.HTML(value=_SPINNER if visible else "", visible=visible)
