<!-- /docs/design.md -->
# Design Notes

These notes document the reasoning behind major design choices, focusing on **API usage**, **security considerations**, and **tradeoffs** made during development.

---

## API Notes

- **Anonymous vs Logged-In Flows**  
  - The **anonymous chatbot** relies purely on local rules (`anon_bot/rules.py`) and does not call any external services.  
  - The **logged-in chatbot** integrates with external AIaaS endpoints (e.g., Azure, HuggingFace, or other NLP providers) via modules in `logged_in_bot/` and `agenticcore/providers_unified.py`.  

- **Endpoints**  
  - `/plain-chat` → Anonymous flow; maps to `logic.handle_text`.  
  - `/api/messages` → For framework compatibility (e.g., BotFramework or FastAPI demo).  
  - `/healthz` → Lightweight health check for monitoring.

- **NLU Pipeline**  
  - Intent routing (`nlu/router.py`) determines if user input should be treated as a direct command, a small-talk message, or passed to providers.  
  - Prompts and transformations are managed in `nlu/prompts.py` to centralize natural language templates.

- **Memory Integration**  
  - Session memory stored in `memory/sessions.py`.  
  - Optional RAG indexer (`memory/rag/indexer.py`) allows document retrieval for extended context.

---

## Security Considerations

- **API Keys**  
  - Keys for external services are never hard-coded.  
  - They are pulled from environment variables or `.env` files (via `core/config.py`).  

- **Data Handling**  
  - Anonymous mode never sends user text outside the local process.  
  - Logged-in mode applies guardrails before making external calls.  
  - Sensitive information (emails, IDs) is redacted using `guardrails/pii_redaction.py`.

- **Logging**  
  - Logs are structured (`core/logging.py`) and omit sensitive data by default.  
  - Debug mode can be enabled for local testing but should not be used in production.

- **Privacy**  
  - Anonymous sessions are ephemeral: conversation state is stored only in memory unless explicitly persisted.  
  - Logged-in sessions may optionally persist data, but only with user consent.

---

## Tradeoffs

- **Rule-Based vs AI-Powered**  
  - Rule-based responses are deterministic, fast, and private but limited in sophistication.  
  - AI-powered responses (via providers) allow richer understanding but introduce latency, costs, and privacy risks.  

- **Extensibility vs Simplicity**  
  - Chose a **modular repo structure** (separate folders for `anon_bot`, `logged_in_bot`, `memory`, `nlu`) to allow future growth.  
  - This adds some boilerplate overhead but makes it easier to swap components.

- **Performance vs Accuracy**  
  - Non-functional requirement: responses within 2 seconds for 95% of requests.  
  - This meant prioritizing lightweight providers and caching over heavyweight models.  

- **Anonymous Mode as Default**  
  - Defaulting to anonymous mode ensures the system works offline and avoids external dependencies.  
  - Tradeoff: limits functionality until the user explicitly opts in for a logged-in session.

---

## Summary

The design balances **privacy, modularity, and extensibility**. By cleanly separating anonymous and logged-in paths, the system can run entirely offline while still supporting richer AI features when configured. Security and privacy are first-class concerns, and tradeoffs were made to keep the system lightweight, testable, and compliant with project constraints.

## Documentation

- [Brief Academic Write Up](Brief_Academic_Write_Up.md)
- [README](../README.md)
- [Architecture Overview](architecture.md)  
- [Design Notes](design.md) 
- [Developer & Build/Test Guide](Developer_Guide_Build_Test.md) 
- [Implementation Notes](storefront/IMPLEMENTATION.md) 
- [Dev Doc](DEV_DOC.md)  
- [Developer Guide Build Test](Developer_Guide_Build_Test.md) 