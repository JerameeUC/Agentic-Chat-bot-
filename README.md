<!-- README.md -->
# Agentic-Chat-bot-
Agentic Chat-bot with RAG, Memory, and Privacy Considerations. 

# Storefront Chatbot

This repo follows a modular layout with a Gradio UI, NLU pipeline, anonymous and logged-in flows,
guardrails, and optional Azure sentiment.

## Quickstart
```bash
make dev
make run
# open http://localhost:7860
```

## Agentic Integration
- Core bot: `agenticcore/chatbot/services.py`
- Providers: `agenticcore/providers_unified.py`
- CLI: `python -m agenticcore.cli agentic "hello"` (loads .env)
- FastAPI demo: `uvicorn integrations.web.fastapi.web_agentic:app --reload`

## Added Samples & Tests
- chat.html → `app/assets/html/chat.html`
- echo_bot.py → `integrations/botframework/bots/echo_bot.py`
- ChatbotIntegration.ipynb → `notebooks/ChatbotIntegration.ipynb`
- SimpleTraditionalChatbot.ipynb → `notebooks/SimpleTraditionalChatbot.ipynb`
- smoke_test.py → `tests/smoke_test.py`
- test_routes.py → `tests/test_routes.py`
- quick_sanity.py → `tools/quick_sanity.py`
- example.py → `examples/example.py`
- service.py → `samples/service.py`
- DEV_DOC.md → `docs/DEV_DOC.md`

Run `pytest -q` for tests; open HTML in `app/assets/html/` to try local UIs.


---
This is the **unified** storefront-chatbot bundle.
Duplicates from earlier skeletons were removed; priority order was:
1) storefront_chatbot_final_bundle
2) storefront_chatbot_merged_with_agentic
3) storefront_chatbot_skeleton
