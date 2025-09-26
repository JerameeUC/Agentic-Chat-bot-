# Storefront Chatbot (Unified)

This merges your skeleton with AgenticCore + a simple FastAPI backend and frontends.

## Run
1) python -m venv .venv && source .venv/bin/activate
2) pip install -r requirements.txt
3) uvicorn backend.app.main:app --reload --port 8000
4) Open http://127.0.0.1:8000/ui or open frontend/chat_minimal.html

## Test
- pytest -q
- python tools/smoke_test.py
