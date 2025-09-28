# app/components/ProductCard.py
import gradio as gr
from html import escape

def render_product_card(p: dict) -> gr.HTML:
    """
    Render a simple product dict with keys:
      id, name, description, price, currency, tags
    """
    name = escape(str(p.get("name", "")))
    desc = escape(str(p.get("description", "")))
    price = p.get("price", "")
    currency = escape(str(p.get("currency", "USD")))
    tags = p.get("tags") or []
    tags_html = " ".join(
        f"<span style='border:1px solid #e2e8f0;padding:2px 6px;border-radius:999px;font-size:12px;color:#334155'>{escape(str(t))}</span>"
        for t in tags
    )
    html = f"""
    <div style="border:1px solid #e2e8f0;border-radius:12px;padding:12px">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div style="font-weight:600;color:#0f172a">{name}</div>
        <div style="color:#0f172a;font-weight:600">{price} {currency}</div>
      </div>
      <div style="color:#334155;margin:6px 0 10px;line-height:1.5">{desc}</div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">{tags_html}</div>
    </div>
    """
    return gr.HTML(value=html)
