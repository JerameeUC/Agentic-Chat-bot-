import os
import gradio as gr
from transformers import pipeline

# --- Storefront integration -----------------------------------------------
# Place storefront_rules.py + storefront_data.json in agenticcore/
# If you temporarily keep them beside this file, change the import to:
#   from storefront_rules import load_storefront, answer_faq, get_parking_rules, get_venue_rules, search_products
try:
    from agenticcore.storefront_rules import (
        load_storefront,
        answer_faq,
        get_parking_rules,
        get_venue_rules,
        search_products,
    )
    _STORE_DATA = load_storefront()  # auto-loads storefront_data.json
except Exception as _e:
    # Soft-fail: storefront answers disabled if module/data not present.
    _STORE_DATA = None

def try_storefront_answer(user_text: str) -> str | None:
    """Return a storefront/rules/product answer if we can; else None."""
    if not _STORE_DATA:
        return None

    # 1) FAQ direct match
    ans = answer_faq(_STORE_DATA, user_text)
    if ans:
        return ans

    # 2) Rules by keywords
    lt = (user_text or "").lower()
    if "parking rule" in lt or ("parking" in lt and "rule" in lt):
        rules = get_parking_rules(_STORE_DATA)
        if rules:
            return "Parking rules:\n- " + "\n- ".join(rules)
    if "venue rule" in lt or ("venue" in lt and "rule" in lt) or "dress code" in lt or "attire" in lt:
        rules = get_venue_rules(_STORE_DATA)
        if rules:
            return "Venue rules:\n- " + "\n- ".join(rules)

    # 3) Product lookup
    hits = search_products(_STORE_DATA, user_text)
    if hits:
        lines = []
        for p in hits:
            price = p.get("price_usd")
            desc = p.get("description", "")
            name = p.get("name", "Item")
            if isinstance(price, (int, float)):
                lines.append(f"{name} — ${price:.2f}: {desc}")
            else:
                lines.append(f"{name}: {desc}")
        return "\n".join(lines)

    return None
# ---------------------------------------------------------------------------

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

def chat_pipeline(message, max_new_tokens=128, temperature=0.8, top_p=0.95):
    """
    1) Try storefront knowledge (products/rules/FAQ)
    2) Fallback to model generation with the same sliders
    """
    sf = try_storefront_answer(message)
    if sf:
        return sf
    return chat_fn(message, max_new_tokens=max_new_tokens, temperature=temperature, top_p=top_p)

with gr.Blocks(title="Agentic-Chat-bot") as demo:
    gr.Markdown("# 🤖 Agentic Chat Bot\nGradio + Transformers demo")
    prompt = gr.Textbox(label="Prompt", placeholder="Ask me anything…", lines=4)
    out = gr.Textbox(label="Response", lines=6)
    max_new = gr.Slider(32, 512, 128, 1, label="Max new tokens")
    temp = gr.Slider(0.1, 1.5, 0.8, 0.05, label="Temperature")
    topp = gr.Slider(0.1, 1.0, 0.95, 0.05, label="Top-p")
    btn = gr.Button("Send")

    # Use chat_pipeline so storefront answers are returned instantly when applicable
    btn.click(chat_pipeline, [prompt, max_new, temp, topp], out)
    prompt.submit(chat_pipeline, [prompt, max_new, temp, topp], out)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
