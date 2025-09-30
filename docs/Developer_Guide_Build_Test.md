<!-- /docs/Developer_Guide_Build_Test.md -->
# Developer & Build/Test Guide

## Purpose & Scope
This document combines the Developer Guide and Build & Test Guide. It explains the repository structure, endpoints, CLI, providers, and step‑by‑step build/test instructions.

---

## Architecture Overview
- **UI:** Gradio Blocks UI and plain HTML testers.
- **Router/Logic:** Routes text to anon/logged-in/agentic paths.
- **NLU:** Intent router and prompt manager.
- **Memory:** Session handling and optional RAG retriever.
- **Guardrails:** PII redaction and safety filters.
- **Providers:** Cloud/offline AI providers.

---

## Repository Layout
- `app/` – AIOHTTP server + UI components.
- `anon_bot/` – Anonymous rule-based bot.
- `logged_in_bot/` – Provider-backed logic.
- `nlu/` – Pipeline, router, prompts.
- `memory/` – Session store + retriever.
- `guardrails/` – PII/safety enforcement.
- `agenticcore/` – Unified provider integrations.

---

## Services & Routes
- `GET /healthz` – health check.
- `POST /plain-chat` – anon chat endpoint.
- `POST /api/messages` – Bot Framework activities.
- `GET /agentic` (FastAPI) – provider-backed demo.

### Health Check Examples
```bash
curl http://127.0.0.1:3978/healthz
curl -X POST http://127.0.0.1:3978/plain-chat -H "Content-Type: application/json" -d '{"text":"reverse hello"}'
```

---

## CLI
- `python -m agenticcore.cli agentic "hello"`
- `python -m agenticcore.cli status`

---

## Providers
Configured via environment variables (HF, Azure, OpenAI, Cohere, DeepAI). Offline fallback included.

### Environment Variables
- Hugging Face: `HF_API_KEY`, `HF_MODEL_SENTIMENT`
- Azure: `MICROSOFT_AI_SERVICE_ENDPOINT`, `MICROSOFT_AI_API_KEY`
- OpenAI: `OPENAI_API_KEY`
- Cohere: `COHERE_API_KEY`
- DeepAI: `DEEPAI_API_KEY`

If no keys are set, the system falls back to **offline sentiment mode**.

---

## Build Instructions

### Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Run AIOHTTP Backend
```bash
python app/app.py
```

### Run Gradio UI
```bash
export APP_MODE=gradio
python app/app.py
```

### Run FastAPI Demo
```bash
uvicorn agenticcore.web_agentic:app --reload --port 8000
```

---

## Testing

### Automated Tests
```bash
pytest -q
pytest -q tests/test_anon_bot.py
pytest -q tests/test_routes.py
```

### Manual Tests
```bash
curl http://127.0.0.1:3978/healthz
curl -X POST http://127.0.0.1:3978/plain-chat -H "Content-Type: application/json" -d '{"text":"reverse hello"}'
```

---

## Troubleshooting
- Missing provider keys → falls back to offline.
- HTML tester fails → confirm backend running.
- If provider calls fail → run CLI with `status` to confirm API keys.

---

## Security Defaults
- No keys in repo.
- Anon mode is offline.
- Logged-in mode applies guardrails.

---

_Audience: Contributors & Developers_
