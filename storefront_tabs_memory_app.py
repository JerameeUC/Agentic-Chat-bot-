# storefront_tabs_memory_app.py
import os, json
import gradio as gr
from transformers import pipeline

# ---------------- Model ----------------
MODEL_NAME = os.getenv("HF_MODEL_GENERATION", "distilgpt2")
_pipe = None
def _get_pipe():
    global _pipe
    if _pipe is None:
        _pipe = pipeline("text-generation", model=MODEL_NAME)
    return _pipe

def model_generate(prompt, max_new_tokens=128, temperature=0.8, top_p=0.95):
    out = _get_pipe()(
        prompt,
        max_new_tokens=int(max_new_tokens),
        do_sample=True,
        temperature=float(temperature),
        top_p=float(top_p),
        pad_token_id=50256,
    )
    return out[0]["generated_text"]


# ---------------- Storefront knowledge (helper module preferred) ----------------
STORE_DATA, USE_HELPERS = None, False
try:
    # Optional helper module under agenticcore/
    from agenticcore.storefront_rules import (
        load_storefront, answer_faq, get_parking_rules, get_venue_rules, search_products
    )
    STORE_DATA = load_storefront()
    USE_HELPERS = True
except Exception:
    # Fallback: try JSON next to this file or under agenticcore/
    CANDIDATES = [
        os.path.join(os.path.dirname(__file__), "storefront_data.json"),
        os.path.join(os.path.dirname(__file__), "agenticcore", "storefront_data.json"),
    ]
    for p in CANDIDATES:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                STORE_DATA = json.load(f)
            break

# Defaults if JSON/module missing
DEFAULT_PRODUCTS = [
    {"SKU": "CG-SET", "Name": "Cap & Gown Set", "Price": 59.00, "Notes": "Tassel included; ship until 10 days before event"},
    {"SKU": "PK-1",   "Name": "Parking Pass",   "Price": 10.00, "Notes": "Multiple passes allowed per student"},
]
DEFAULT_PARKING = ["No double parking.", "Vehicles parked in handicap will be towed."]
DEFAULT_VENUE   = ["Formal attire recommended (not required).", "No muscle shirts.", "No sagging pants."]

# Normalize JSON to tables for the UI
if STORE_DATA:
    try:
        DEFAULT_PRODUCTS = [{
            "SKU": p.get("sku",""),
            "Name": p.get("name",""),
            "Price": p.get("price_usd",""),
            "Notes": (p.get("description") or "")[:120],
        } for p in STORE_DATA.get("products", [])]
        DEFAULT_PARKING = STORE_DATA.get("policies", {}).get("parking_rules", DEFAULT_PARKING) or DEFAULT_PARKING
        DEFAULT_VENUE   = STORE_DATA.get("policies", {}).get("venue_rules", DEFAULT_VENUE)     or DEFAULT_VENUE
    except Exception:
        pass


# ---------------- Memory seeding ----------------
def seed_storefront_facts() -> str:
    """Small system-like primer injected ahead of chat history to bias the LLM toward storefront truth."""
    lines = ["You are answering questions about a graduation storefront.",
             "Products:"]
    for p in DEFAULT_PRODUCTS:
        price = p.get("Price")
        if isinstance(price, (int, float)):
            price = f"${price:.2f}"
        lines.append(f"- {p.get('Name','Item')} ({p.get('SKU','')}) — {price}: {p.get('Notes','')}")
    lines.append("Venue rules:")
    for r in DEFAULT_VENUE:
        lines.append(f"- {r}")
    lines.append("Parking rules:")
    for r in DEFAULT_PARKING:
        lines.append(f"- {r}")
    lines.append("Answer concisely using these facts. If unsure, say what’s known from the list above.")
    return "\n".join(lines)

SEED_TEXT = seed_storefront_facts()

def build_prompt_from_history(history, user_text, k=4):
    """history = [[user, bot], ...] — build a short rolling prompt + seed facts."""
    lines = [SEED_TEXT, "", "Conversation so far:"]
    for u, b in (history or [])[-k:]:
        if u: lines.append(f"User: {u}")
        if b: lines.append(f"Assistant: {b}")
    lines.append(f"User: {user_text}")
    lines.append("Assistant:")
    return "\n".join(lines)


# ---------------- Storefront Q&A router (storefront first, then LLM) ----------------
def storefront_qna(text: str) -> str | None:
    t = (text or "").lower().strip()
    if not t:
        return None

    # Single-word catches to avoid LLM drift
    if t in {"parking"}:
        return "Parking rules:\n- " + "\n- ".join(DEFAULT_PARKING)
    if t in {"venue", "attire", "dress", "dress code"}:
        return "Venue rules:\n- " + "\n- ".join(DEFAULT_VENUE)
    if t in {"passes", "parking pass", "parking passes"}:
        return "Yes, multiple parking passes are allowed per student."

    # Prefer helper functions if available
    if USE_HELPERS and STORE_DATA:
        a = answer_faq(STORE_DATA, t)
        if a:
            return a
        if "parking" in t and "rule" in t:
            r = get_parking_rules(STORE_DATA)
            if r:
                return "Parking rules:\n- " + "\n- ".join(r)
        if ("venue" in t and "rule" in t) or "attire" in t or "dress code" in t:
            r = get_venue_rules(STORE_DATA)
            if r:
                return "Venue rules:\n- " + "\n- ".join(r)
        # Specific timing phrasing to avoid hallucinated dates
        if "parking" in t and ("hours" in t or "time" in t or "open" in t):
            return "Parking lots open 2 hours before the ceremony."
        hits = search_products(STORE_DATA, t)
        if hits:
            return "\n".join(
                f"{p.get('name','Item')} — ${p.get('price_usd',0):.2f}: {p.get('description','')}"
                for p in hits
            )
        return None

    # Fallback rules (no helper module)
    if "parking" in t and ("more than one" in t or "multiple" in t or "extra" in t):
        return "Yes, multiple parking passes are allowed per student."
    if "parking" in t and "rule" in t:
        return "Parking rules:\n- " + "\n- ".join(DEFAULT_PARKING)
    if "parking" in t and ("hours" in t or "time" in t or "open" in t):
        return "Parking lots open 2 hours before the ceremony."
    if "attire" in t or "dress code" in t or ("venue" in t and "rule" in t):
        return "Venue rules:\n- " + "\n- ".join(DEFAULT_VENUE)
    if "cap" in t or "gown" in t:
        return "\n".join(
            f"{p['Name']} — ${p['Price']:.2f}: {p['Notes']}"
            for p in DEFAULT_PRODUCTS
        )
    return None


def chat_pipeline(history, message, max_new_tokens=128, temperature=0.8, top_p=0.95):
    # 1) Try storefront knowledge first
    sf = storefront_qna(message)
    if sf:
        return sf
    # 2) Memory-aware model prompt
    prompt = build_prompt_from_history(history, message, k=4)
    return model_generate(prompt, max_new_tokens, temperature, top_p)


# ---------------- Gradio UI (Tabs + Accordion) ----------------
CSS = """
:root { --bg:#0b0d12; --panel:#0f172a; --border:#1f2940; --text:#e5e7eb; --muted:#9ca3af; }
.gradio-container { background: var(--bg) !important; color: var(--text) !important; }
.panel { border:1px solid var(--border); border-radius:16px; background:var(--panel); }
.small { font-size:12px; color: var(--muted); }
"""

with gr.Blocks(title="Storefront Chat", css=CSS) as demo:
    gr.Markdown("## Storefront Chat")

    # Keep a single source of truth for chat history (pairs of [user, bot])
    history_state = gr.State([])

    with gr.Tabs():
        # --- TAB 1: Chat (sliders tucked into an accordion) ---
        with gr.TabItem("Chat"):
            with gr.Group(elem_classes=["panel"]):
                chat = gr.Chatbot(height=360, bubble_full_width=False, label="Chat")

                with gr.Row():
                    msg = gr.Textbox(placeholder="Ask about parking rules, attire, cap & gown, pickup times…", scale=5)
                    send = gr.Button("Send", scale=1)

                # Quick chips
                with gr.Row():
                    chip1 = gr.Button("Parking rules", variant="secondary")
                    chip2 = gr.Button("Multiple passes", variant="secondary")
                    chip3 = gr.Button("Attire", variant="secondary")
                    chip4 = gr.Button("When do lots open?", variant="secondary")

                # Advanced options hidden
                with gr.Accordion("Advanced chat options", open=False):
                    max_new = gr.Slider(32, 512, 128, 1, label="Max new tokens")
                    temp    = gr.Slider(0.1, 1.5, 0.8, 0.05, label="Temperature")
                    topp    = gr.Slider(0.1, 1.0, 0.95, 0.05, label="Top-p")

                # Small utilities
                with gr.Row():
                    health_btn = gr.Button("Health", variant="secondary")
                    caps_btn   = gr.Button("Capabilities", variant="secondary")
                    status_md  = gr.Markdown("Status: not checked", elem_classes=["small"])

        # --- TAB 2: Products ---
        with gr.TabItem("Products"):
            gr.Markdown("### Available Items")
            cols = list(DEFAULT_PRODUCTS[0].keys()) if DEFAULT_PRODUCTS else ["SKU","Name","Price","Notes"]
            data = [[p.get(c,"") for c in cols] for p in DEFAULT_PRODUCTS]
            _products_tbl = gr.Dataframe(headers=cols, value=data, interactive=False, wrap=True, label="Products")

        # --- TAB 3: Rules ---
        with gr.TabItem("Rules"):
            gr.Markdown("### Venue rules")
            gr.Markdown("- " + "\n- ".join(DEFAULT_VENUE))
            gr.Markdown("### Parking rules")
            gr.Markdown("- " + "\n- ".join(DEFAULT_PARKING))

        # --- TAB 4: Logistics ---
        with gr.TabItem("Logistics"):
            gr.Markdown(
                "### Event Logistics\n"
                "- Shipping available until 10 days before event (typ. 3–5 business days)\n"
                "- Pickup: Student Center Bookstore during the week prior to event\n"
                "- Graduates arrive 90 minutes early; guests 60 minutes early\n"
                "- Lots A & B open 2 hours before; overflow as needed\n"
                "\n*Try asking the bot:* “What time should I arrive?” • “Where do I pick up the gown?”"
            )

    # ---------- Helpers that keep Chatbot history valid (list of [u,b]) ----------
    def _append_bot_md(history, md_text):
        """Append a bot markdown message without breaking the [user, bot] format."""
        history = history or []
        return history + [[None, md_text]]

    # ---------- Callbacks ----------
    def on_send(history, message, max_new_tokens, temperature, top_p):
        t = (message or "").strip()
        if not t:
            return history, history, ""  # no-op
        history = (history or []) + [[t, None]]
        reply = chat_pipeline(history[:-1], t, max_new_tokens, temperature, top_p)
        history[-1][1] = reply
        # Return updated state AND what the Chatbot should render
        return history, history, ""

    def _health_cb(history):
        md = (f"### Status: ✅ Healthy\n"
              f"- Model: `{MODEL_NAME}`\n"
              f"- Storefront module: {'yes' if USE_HELPERS else 'no'}\n"
              f"- Storefront JSON: {'loaded' if bool(STORE_DATA) else 'not found'}")
        new_hist = _append_bot_md(history, md)
        return new_hist, new_hist, "Status: ✅ Healthy"

    def _caps_cb(history):
        caps = [
            "Chat (LLM text-generation, memory-aware prompt)",
            "Storefront Q&A (parking, attire, products, logistics)",
            "Adjustable: max_new_tokens, temperature, top-p",
        ]
        md = "### Capabilities\n- " + "\n- ".join(caps)
        new_hist = _append_bot_md(history, md)
        return new_hist, new_hist

    # Wire up (note: always update both the state and the Chatbot value)
    send.click(on_send, [history_state, msg, max_new, temp, topp], [history_state, chat, msg])
    msg.submit(on_send, [history_state, msg, max_new, temp, topp], [history_state, chat, msg])

    # Chips
    chip1.click(lambda: "What are the parking rules?", outputs=msg)
    chip2.click(lambda: "Can I buy multiple parking passes?", outputs=msg)
    chip3.click(lambda: "Is formal attire required?", outputs=msg)
    chip4.click(lambda: "What time do the parking lots open?", outputs=msg)

    # Health / capabilities (append to chat, keep valid tuple format)
    health_btn.click(_health_cb, inputs=[history_state], outputs=[history_state, chat, status_md])
    caps_btn.click(_caps_cb, inputs=[history_state], outputs=[history_state, chat])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
