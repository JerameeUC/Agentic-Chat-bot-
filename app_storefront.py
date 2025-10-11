# app_storefront.py
import os
import sys
import gradio as gr

# Ensure "core/" is importable
sys.path.append(os.path.join(os.path.dirname(__file__), "core"))

# Import only functions; core.storefront doesn't export constants
from core.model import model_generate, MODEL_NAME
from core.memory import build_prompt_from_history
from core.storefront import load_storefront, storefront_qna, extract_products, get_rules
from core.storefront import is_storefront_query

def chat_pipeline(history, message, max_new_tokens=96, temperature=0.7, top_p=0.9):
    # 1) Try storefront facts first
    sf = storefront_qna(DATA, message)
    if sf:
        return sf

    # 2) If not a storefront query, offer guided help (no LLM)
    if not is_storefront_query(message):
        return (
            "I can help with the graduation storefront. Examples:\n"
            "- Parking rules, lots opening times\n"
            "- Attire / dress code\n"
            "- Cap & Gown details and pickup\n"
            "- Parking passes (multiple allowed)\n"
            "Ask one of those, and I’ll answer directly."
        )

    # 3) Otherwise, generate with memory and hard stops
    prompt = build_prompt_from_history(history, message, k=4)
    gen = model_generate(prompt, max_new_tokens, temperature, top_p)
    return clean_generation(gen)

def clean_generation(text: str) -> str:
    return (text or "").strip()

# ---------------- Load data + safe fallbacks ----------------
DATA = load_storefront()  # may be None if storefront_data.json missing/empty

# Fallbacks used if JSON not present
FALLBACK_PRODUCTS = [
    {"sku": "CG-SET", "name": "Cap & Gown Set", "price": 59.00,
     "notes": "Tassel included; ships until 10 days before the event"},
    {"sku": "PK-1",   "name": "Parking Pass",   "price": 10.00,
     "notes": "Multiple passes are allowed per student"}
]
FALLBACK_VENUE = [
    "Formal attire recommended (not required).",
    "No muscle shirts.",
    "No sagging pants."
]
FALLBACK_PARKING = [
    "No double parking.",
    "Vehicles parked in handicap spaces will be towed."
]

# Normalize products/rules for the tabs
if DATA:
    PRODUCTS = extract_products(DATA) or FALLBACK_PRODUCTS
    venue_rules, parking_rules = get_rules(DATA)
    VENUE_RULES = venue_rules or FALLBACK_VENUE
    PARKING_RULES = parking_rules or FALLBACK_PARKING
else:
    PRODUCTS = FALLBACK_PRODUCTS
    VENUE_RULES = FALLBACK_VENUE
    PARKING_RULES = FALLBACK_PARKING



# ---------------- UI ----------------
CSS = """
:root { --bg:#0b0d12; --panel:#0f172a; --border:#1f2940; --text:#e5e7eb; --muted:#9ca3af; }
.gradio-container { background: var(--bg) !important; color: var(--text) !important; }
.panel { border:1px solid var(--border); border-radius:16px; background:var(--panel); }
.small { font-size:12px; color: var(--muted); }
"""

with gr.Blocks(title="Storefront Chat", css=CSS) as demo:
    gr.Markdown("## Storefront Chat")

    # Single history state (kept in sync with Chatbot)
    history_state = gr.State([])

    with gr.Tabs():
        # --- TAB: Chat ---
        with gr.TabItem("Chat"):
            with gr.Group(elem_classes=["panel"]):
                chat = gr.Chatbot(height=360, bubble_full_width=False, label="Chat")

                with gr.Row():
                    msg  = gr.Textbox(placeholder="Ask about parking rules, attire, cap & gown, pickup times…", scale=5)
                    send = gr.Button("Send", scale=1)

                # Quick chips
                with gr.Row():
                    chip1 = gr.Button("Parking rules", variant="secondary")
                    chip2 = gr.Button("Multiple passes", variant="secondary")
                    chip3 = gr.Button("Attire", variant="secondary")
                    chip4 = gr.Button("When do lots open?", variant="secondary")

                # Advanced options (sliders + Health/Capabilities)
                with gr.Accordion("Advanced chat options", open=False):
                    max_new = gr.Slider(32, 512, 128, 1, label="Max new tokens")
                    temp    = gr.Slider(0.1, 1.5, 0.8, 0.05, label="Temperature")
                    topp    = gr.Slider(0.1, 1.0, 0.95, 0.05, label="Top-p")

                    with gr.Row():
                        health_btn = gr.Button("Health", variant="secondary")
                        caps_btn   = gr.Button("Capabilities", variant="secondary")
                        status_md  = gr.Markdown("Status: not checked", elem_classes=["small"])

        # --- TAB: Products ---
        with gr.TabItem("Products"):
            gr.Markdown("### Available Items")
            cols = ["sku", "name", "price", "notes"]
            data = [[p.get(c, "") for c in cols] for p in PRODUCTS]
            gr.Dataframe(headers=[c.upper() for c in cols], value=data, interactive=False, wrap=True, label="Products")

        # --- TAB: Rules ---
        with gr.TabItem("Rules"):
            gr.Markdown("### Venue rules")
            gr.Markdown("- " + "\n- ".join(VENUE_RULES))
            gr.Markdown("### Parking rules")
            gr.Markdown("- " + "\n- ".join(PARKING_RULES))

        # --- TAB: Logistics ---
        with gr.TabItem("Logistics"):
            gr.Markdown(
                "### Event Logistics\n"
                "- Shipping available until 10 days before event (typ. 3–5 business days)\n"
                "- Pickup: Student Center Bookstore during the week prior to event\n"
                "- Graduates arrive 90 minutes early; guests 60 minutes early\n"
                "- Lots A & B open 2 hours before; overflow as needed\n"
                "\n*Try asking the bot:* “What time should I arrive?” • “Where do I pick up the gown?”"
            )

    # ---------- Helpers ----------
    def _append_bot_md(history, md_text):
        history = history or []
        return history + [[None, md_text]]

    # ---------- Callbacks ----------
    def on_send(history, message, max_new_tokens, temperature, top_p):
        t = (message or "").strip()
        if not t:
            return history, history, ""  # no-op; shapes must match
        history = (history or []) + [[t, None]]
        reply = chat_pipeline(history[:-1], t, max_new_tokens, temperature, top_p)
        history[-1][1] = reply
        return history, history, ""

    def _health_cb(history):
        md = (
            f"### Status: ✅ Healthy\n"
            f"- Model: `{MODEL_NAME}`\n"
            f"- Storefront JSON: {'loaded' if bool(DATA) else 'not found'}"
        )
        new_hist = _append_bot_md(history, md)
        return new_hist, new_hist, "Status: ✅ Healthy"

    def _caps_cb(history):
        md = (
            "### Capabilities\n"
            "- Chat (LLM text-generation, memory-aware prompt)\n"
            "- Storefront Q&A (parking, attire, products, logistics)\n"
            "- Adjustable: max_new_tokens, temperature, top-p"
        )
        new_hist = _append_bot_md(history, md)
        return new_hist, new_hist

    # Wire up (state + chatbot)
    send.click(on_send, [history_state, msg, max_new, temp, topp], [history_state, chat, msg])
    msg.submit(on_send, [history_state, msg, max_new, temp, topp], [history_state, chat, msg])

    # Chips → prefill textbox
    chip1.click(lambda: "What are the parking rules?", outputs=msg)
    chip2.click(lambda: "Can I buy multiple parking passes?", outputs=msg)
    chip3.click(lambda: "Is formal attire required?", outputs=msg)
    chip4.click(lambda: "What time do the parking lots open?", outputs=msg)

    # Health / Capabilities live inside Advanced
    health_btn.click(_health_cb, inputs=[history_state], outputs=[history_state, chat, status_md])
    caps_btn.click(_caps_cb,   inputs=[history_state], outputs=[history_state, chat])

def clean_generation(text: str) -> str:
    s = (text or "").strip()

    # If the prompt contained "Assistant:", keep only what comes after the last one
    last = s.rfind("Assistant:")
    if last != -1:
        s = s[last + len("Assistant:"):].strip()

    # If it accidentally continued into a new "User:" or instructions, cut there
    cut_marks = ["\nUser:", "\nYOU ARE ANSWERING", "\nProducts:", "\nVenue rules:", "\nParking rules:"]
    cut_positions = [s.find(m) for m in cut_marks if s.find(m) != -1]
    if cut_positions:
        s = s[:min(cut_positions)].strip()

    # Collapse repeated lines like "Yes, multiple parking passes..." spam
    lines, out = s.splitlines(), []
    seen = set()
    for ln in lines:
        # dedupe only exact consecutive repeats; keep normal conversation lines
        if not out or ln != out[-1]:
            out.append(ln)
    return "\n".join(out).strip()

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
