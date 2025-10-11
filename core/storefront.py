# core/storefront.py
import json, os

def clean_generation(text: str) -> str:
    s = (text or "").strip()

    # Keep only text after the last "Assistant:"
    last = s.rfind("Assistant:")
    if last != -1:
        s = s[last + len("Assistant:"):].strip()

    # Cut at the first sign of a new turn or meta
    cut_marks = ["\nUser:", "\nSystem:", "\n###", "\nProducts:", "\nVenue rules:", "\nParking rules:"]
    cuts = [s.find(m) for m in cut_marks if s.find(m) != -1]
    if cuts:
        s = s[:min(cuts)].strip()

    # Remove egregious token loops like "Account/Account/..."
    s = re.sub(r"(?:\b([A-Z][a-zA-Z0-9_/.-]{2,})\b(?:\s*/\s*\1\b)+)", r"\1", s)

    # Collapse consecutive duplicate lines
    dedup = []
    for ln in s.splitlines():
        if not dedup or ln.strip() != dedup[-1].strip():
            dedup.append(ln)
    return "\n".join(dedup).strip()

HELP_KEYWORDS = {
    "help", "assist", "assistance", "tips", "how do i", "what can you do",
    "graduation help", "help me with graduation", "can you help me with graduation"
}

STORE_KEYWORDS = {
    "cap", "gown", "parking", "pass", "passes", "attire", "dress",
    "venue", "logistics", "shipping", "pickup", "lot", "lots", "arrival", "size", "sizing"
}

def is_storefront_query(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in STORE_KEYWORDS) or any(k in t for k in HELP_KEYWORDS)

def _get_lots_open_hours(data) -> int:
    try:
        return int(((data or {}).get("logistics") or {}).get("lots_open_hours_before") or 2)
    except Exception:
        return 2

# Main router (drop-in)
def storefront_qna(data, user_text: str) -> str | None:
    """
    Deterministic storefront answers first:
      - single-word intents (parking / wear / passes)
      - help/capability prompt
      - FAQ (if you have answer_faq)
      - explicit rules queries
      - 'lots open' timing
      - compact products list
    Returns None to allow LLM fallback in your chat pipeline.
    """
    if not user_text:
        return None
    t = user_text.strip().lower()

    # 1) Single-word / exact intents to avoid LLM hallucinations
    if t in {"parking"}:
        _, pr = get_rules(data)
        if pr:
            return "Parking rules:\n- " + "\n- ".join(pr)

    # Map 'wear/attire' variants directly to venue rules
    if t in {"venue", "attire", "dress", "dress code", "wear"} or "what should i wear" in t:
        vr, _ = get_rules(data)
        if vr:
            return "Venue rules:\n- " + "\n- ".join(vr)

    # Parking passes (multiple allowed)
    if t in {"passes", "parking pass", "parking passes"}:
        return "Yes, multiple parking passes are allowed per student."

    # 2) Help / capability intent → deterministic guidance
    if any(k in t for k in HELP_KEYWORDS):
        return (
            "I can help with the graduation storefront. Try:\n"
            "- “What are the parking rules?”\n"
            "- “Can I buy multiple parking passes?”\n"
            "- “Is formal attire required?”\n"
            "- “Where do I pick up the gown?”\n"
            "- “When do lots open?”"
        )

    # 3) JSON-driven FAQ (if available)
    try:
        a = answer_faq(data, t)
        if a:
            return a
    except Exception:
        pass  # answer_faq may not exist or data may be None

    # 4) Explicit rules phrasing (keeps answers tight and consistent)
    if "parking" in t and "rule" in t:
        _, pr = get_rules(data)
        if pr:
            return "Parking rules:\n- " + "\n- ".join(pr)

    if ("venue" in t and "rule" in t) or "attire" in t or "dress code" in t:
        vr, _ = get_rules(data)
        if vr:
            return "Venue rules:\n- " + "\n- ".join(vr)

    # 5) “When do lots open?” / hours / time
    if "parking" in t and ("hours" in t or "time" in t or "open" in t):
        lots_open = _get_lots_open_hours(data)
        return f"Parking lots open {lots_open} hours before the ceremony."

    # 6) Product info (cap/gown/parking pass)
    if any(k in t for k in ("cap", "gown", "parking pass", "product", "item", "price")):
        prods = extract_products(data)
        if prods:
            lines = []
            for p in prods:
                name = p.get("name", "Item")
                price = p.get("price", p.get("price_usd", ""))
                notes = p.get("notes", p.get("description", ""))
                price_str = f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
                lines.append(f"{name} — {price_str}: {notes}")
            return "\n".join(lines)

    # No deterministic match → let the caller fall back to the LLM
    return None

def _find_json():
    candidates = [
        os.path.join(os.getcwd(), "storefront_data.json"),
        os.path.join(os.getcwd(), "agenticcore", "storefront_data.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

def load_storefront():
    p = _find_json()
    if not p:
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def _string_in_any(s, variants):
    s = s.lower()
    return any(v in s for v in variants)

def answer_faq(data, text: str):
    """Very small FAQ matcher by substring; safe if faq[] missing."""
    faq = (data or {}).get("faq") or []
    t = text.lower()
    for item in faq:
        qs = item.get("q") or []
        if any(q.lower() in t for q in qs):
            return item.get("a")
    return None

def extract_products(data):
    prods = []
    for p in (data or {}).get("products", []):
        prods.append({
            "sku": p.get("sku",""),
            "name": p.get("name",""),
            "price": p.get("price_usd",""),
            "notes": (p.get("description") or "")[:140],
        })
    return prods

def get_rules(data):
    pol = (data or {}).get("policies", {}) or {}
    return pol.get("venue_rules", []), pol.get("parking_rules", [])
