<!-- README.md -->
---
title: Agentic Chat Bot
emoji: 👁
colorFrom: gray
colorTo: blue
sdk: gradio
sdk_version: 5.49.0
app_file: app.py
pinned: false
license: mit
short_description: Agentic Chat-bot with RAG, Memory, and Privacy
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

From the original GitHub:

# Agentic Chatbot

Agentic Chatbot with Retrieval-Augmented Generation (RAG), session memory, and privacy guardrails.  
The project follows a **modular architecture** with:
- Gradio UI for interactive demos
- AIOHTTP backend with lightweight routes
- Anonymous and logged-in flows
- Guardrails for safety and PII redaction
- Optional cloud providers (Azure, Hugging Face, OpenAI, Cohere, DeepAI)

---

## Quickstart

Clone the repo, set up a venv, and install dependencies:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Run in dev mode:

```bash
make dev
make run
# open http://localhost:7860 (Gradio UI)
```

Or run the backend directly:

```bash
python app/app.py
```

---

## Health Checks

The AIOHTTP backend exposes simple endpoints:

```bash
curl http://127.0.0.1:3978/healthz
# -> {"status":"ok"}

curl -X POST http://127.0.0.1:3978/plain-chat   -H "Content-Type: application/json"   -d '{"text":"reverse hello"}'
# -> {"reply":"olleh"}
```

---

## Agentic Integration

- **Core bot:** `agenticcore/chatbot/services.py`  
- **Providers:** `agenticcore/providers_unified.py`  
- **CLI:** `python -m agenticcore.cli agentic "hello"` (loads `.env`)  
- **FastAPI demo:**  
  ```bash
  uvicorn integrations.web.fastapi.web_agentic:app --reload --port 8000
  ```

---

## Environment Variables

Provider integrations are selected automatically, or you can pin one with `AI_PROVIDER`. Supported keys:

- Hugging Face: `HF_API_KEY`, `HF_MODEL_SENTIMENT`
- Azure: `MICROSOFT_AI_SERVICE_ENDPOINT`, `MICROSOFT_AI_API_KEY`
- OpenAI: `OPENAI_API_KEY`
- Cohere: `COHERE_API_KEY`
- DeepAI: `DEEPAI_API_KEY`

If no keys are set, the system falls back to **offline sentiment mode**.

---

## Samples & Tests

- **UI samples:**  
  - `app/assets/html/chat.html` – open in browser for local test  
- **Bots:**  
  - `integrations/botframework/bots/echo_bot.py`  
- **Notebooks:**  
  - `notebooks/ChatbotIntegration.ipynb`  
  - `notebooks/SimpleTraditionalChatbot.ipynb`  
- **Tests:**  
  - `tests/smoke_test.py`  
  - `tests/test_routes.py`  
  - `tests/test_anon_bot.py`  
- **Misc:**  
  - `tools/quick_sanity.py`  
  - `examples/example.py`  
  - `samples/service.py`

Run all tests:

```bash
pytest -q
```

---

## Documentation

- [Brief Academic Write Up](docs/Brief_Academic_Write_Up.md)
- [README](../README.md)
- [Architecture Overview](docs/architecture.md)  
- [Design Notes](docs/design.md)  
- [Implementation Notes](docs/storefront/IMPLEMENTATION.md) 
- [Dev Doc](docs/DEV_DOC.md)
- [Developer Guide Build Test](docs/Developer_Guide_Build_Test.md)

---

_Developed for MSAI 631 – Human-Computer Interaction Group Project._
