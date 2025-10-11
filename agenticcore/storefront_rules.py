"""
Storefront rules and product helper for Agentic Chat Bot.
Drop this file into: agenticcore/storefront_rules.py (or anon_bot/storefront_rules.py)
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

DEFAULT_JSON = Path(__file__).parent / "storefront_data.json"

def load_storefront(json_path: Optional[str] = None) -> Dict:
    path = Path(json_path) if json_path else DEFAULT_JSON
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_products(data: Dict) -> List[Dict]:
    return data.get("products", [])

def search_products(data: Dict, query: str) -> List[Dict]:
    q = query.lower()
    return [p for p in get_products(data) if q in p.get("name", "").lower() or q in p.get("category", "").lower()]

def get_parking_rules(data: Dict) -> List[str]:
    return data.get("policies", {}).get("parking_rules", [])

def get_venue_rules(data: Dict) -> List[str]:
    return data.get("policies", {}).get("venue_rules", [])

def answer_faq(data: Dict, question: str) -> Optional[str]:
    q = question.lower().strip("?!. ")
    for item in data.get("faq", []):
        if q in item.get("q", "").lower():
            return item.get("a")
    # simple keyword fallback
    if ("parking" in q) and ("more than one" in q or "multiple" in q):
        return "Yes, multiple parking passes are allowed per student."
    if "attire" in q or "wear" in q or "dress" in q:
        return "Formal attire is recommended but not required. No muscle shirts and no sagging pants."
    if "handicap" in q or "accessible" in q:
        return "Vehicles parked in handicap will be towed. Please use designated accessible spaces with proper permits."
    return None