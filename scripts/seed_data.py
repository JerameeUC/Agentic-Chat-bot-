# /scripts/seed_data.py
#!/usr/bin/env python3
"""
Seed script to load sample products and FAQs into local data files.

- Creates ./data/products.json and ./data/faqs.json
- Provides a CLI to re-seed or show contents
- No external dependencies required

Run:
    python scripts/seed_data.py         # create seed files
    python scripts/seed_data.py show    # print contents
"""

import sys
import json
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_PATH = DATA_DIR / "products.json"
FAQS_PATH = DATA_DIR / "faqs.json"


SAMPLE_PRODUCTS = [
    {
        "id": "p1",
        "name": "Chatbot Pro Subscription",
        "description": "Access advanced features of the chatbot platform.",
        "price": 9.99,
        "currency": "USD",
        "tags": ["subscription", "chatbot"],
    },
    {
        "id": "p2",
        "name": "Custom Bot Avatar",
        "description": "A personalized avatar for your chatbot.",
        "price": 4.99,
        "currency": "USD",
        "tags": ["avatar", "customization"],
    },
    {
        "id": "p3",
        "name": "Analytics Dashboard",
        "description": "Real-time analytics and reporting for your conversations.",
        "price": 14.99,
        "currency": "USD",
        "tags": ["analytics", "dashboard"],
    },
]

SAMPLE_FAQS = [
    {
        "q": "How do I reset my password?",
        "a": "Click 'Forgot password' on the login page and follow the instructions.",
    },
    {
        "q": "Can I export my chat history?",
        "a": "Yes, you can export your chat history from the account settings page.",
    },
    {
        "q": "Do you offer refunds?",
        "a": "Refunds are available within 14 days of purchase. Contact support for help.",
    },
]


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def seed() -> None:
    write_json(PRODUCTS_PATH, SAMPLE_PRODUCTS)
    write_json(FAQS_PATH, SAMPLE_FAQS)
    print(f"✅ Seeded data at {datetime.date.today()} into {DATA_DIR}")


def show() -> None:
    if PRODUCTS_PATH.is_file():
        print("Products:")
        print(PRODUCTS_PATH.read_text(encoding="utf-8"))
    if FAQS_PATH.is_file():
        print("\nFAQs:")
        print(FAQS_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "show":
        show()
    else:
        seed()
