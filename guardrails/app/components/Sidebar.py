# /app/components/Sidebar.py
import gradio as gr

def build_sidebar():
    """
    Returns (mode_dropdown, clear_btn, faq_toggle)
    """
    with gr.Column(scale=1, min_width=220):
        gr.Markdown("### Settings")
        mode = gr.Dropdown(choices=["anonymous", "logged-in"], value="anonymous", label="Mode")
        faq_toggle = gr.Checkbox(label="Show FAQ section", value=False)
        clear = gr.Button("Clear chat")
    return mode, clear, faq_toggle
