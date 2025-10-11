# core/memory.py

META_MARKERS = ("### Status:", "### Capabilities", "Status:", "Capabilities", "Model:", "Storefront JSON:")

def _is_meta(s: str | None) -> bool:
    if not s: return False
    ss = s.strip()
    return any(m in ss for m in META_MARKERS)

def build_prompt_from_history(history, user_text, k=4) -> str:
    """
    history: list[[user, bot], ...] from Gradio Chatbot.
    Keep prompt compact; exclude meta/diagnostic messages.
    """
    lines = [
        "System: Answer questions about the university graduation storefront.",
        "System: Be concise. If unsure, state what is known."
    ]

    # Keep only the last k turns that aren't meta
    kept = []
    for u, b in (history or []):
        if u and not _is_meta(u):
            kept.append(("User", u))
        if b and not _is_meta(b):
            kept.append(("Assistant", b))
    kept = kept[-(2*k):]  # up to k exchanges

    for role, text in kept:
        lines.append(f"{role}: {text}")

    lines.append(f"User: {user_text}")
    lines.append("Assistant:")
    return "\n".join(lines)
