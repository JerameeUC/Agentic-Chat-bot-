# space_app.py
import os
import gradio as gr
from transformers import pipeline

MODEL_NAME = os.getenv("HF_MODEL_GENERATION", "distilgpt2")

_pipe = None
def _get_pipe():
    global _pipe
    if _pipe is None:
        _pipe = pipeline("text-generation", model=MODEL_NAME)
    return _pipe

def chat_fn(message, max_new_tokens=128, temperature=0.8, top_p=0.95):
    message = (message or "").strip()
    if not message:
        return "Please type something!"
    pipe = _get_pipe()
    out = pipe(
        message,
        max_new_tokens=int(max_new_tokens),
        do_sample=True,
        temperature=float(temperature),
        top_p=float(top_p),
        pad_token_id=50256
    )
    return out[0]["generated_text"]

with gr.Blocks(title="Agentic-Chat-bot") as demo:
    gr.Markdown("# 🤖 Agentic Chat Bot\nGradio + Transformers demo")
    prompt = gr.Textbox(label="Prompt", placeholder="Ask me anything…", lines=4)
    out = gr.Textbox(label="Response", lines=6)
    max_new = gr.Slider(32, 512, 128, 1, label="Max new tokens")
    temp = gr.Slider(0.1, 1.5, 0.8, 0.05, label="Temperature")
    topp = gr.Slider(0.1, 1.0, 0.95, 0.05, label="Top-p")
    btn = gr.Button("Send")
    btn.click(chat_fn, [prompt, max_new, temp, topp], out)
    prompt.submit(chat_fn, [prompt, max_new, temp, topp], out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
