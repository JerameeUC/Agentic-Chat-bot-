# app/components/FAQViewer.py
from __future__ import annotations
import gradio as gr
from typing import List, Dict

def build_faq_viewer(faqs: List[Dict[str, str]] | None = None):
    """
    Build a simple searchable FAQ viewer.
    Returns (search_box, results_html, set_data_fn)
    """
    faqs = faqs or []

    search = gr.Textbox(label="Search FAQs", placeholder="Type to filter…")
    results = gr.HTML()

    def _render(query: str):
        q = (query or "").strip().lower()
        items = [f for f in faqs if (q in f["q"].lower() or q in f["a"].lower())] if q else faqs
        if not items:
            return "<em>No results.</em>"
        parts = []
        for f in items[:50]:
            parts.append(
                f"<div style='margin:8px 0;'><b>{f['q']}</b><br/><span style='color:#334155'>{f['a']}</span></div>"
            )
        return "\n".join(parts)

    search.change(fn=_render, inputs=search, outputs=results)
    # Initial render
    results.value = _render("")

    # return a small setter if caller wants to replace faq list later
    def set_data(new_faqs: List[Dict[str, str]]):
        nonlocal faqs
        faqs = new_faqs
        return {results: _render(search.value)}

    return search, results, set_data
