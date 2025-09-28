# app/components/ChatInput.py
from __future__ import annotations
import gradio as gr

def build_chat_input(placeholder: str = "Type a message and press Enter…"):
    """
    Returns (textbox, send_button, clear_button).
    """
    with gr.Row():
        txt = gr.Textbox(placeholder=placeholder, scale=8, show_label=False)
        send = gr.Button("Send", variant="primary", scale=1)
        clear = gr.Button("Clear", scale=1)
    return txt, send, clear
