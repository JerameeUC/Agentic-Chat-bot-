# Anonymous Bot (rule-based, no persistence, with guardrails)

## What this is
- Minimal **rule-based** Python bot
- **Anonymous**: stores no user IDs or history
- **Guardrails**: blocks unsafe topics, redacts PII, caps input length
- **No persistence**: stateless; every request handled fresh

## Run
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --reload