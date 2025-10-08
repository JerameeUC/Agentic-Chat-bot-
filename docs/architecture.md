<!-- /docs/architecture.md -->
# Architecture

This system follows a **modular chatbot architecture** built around a clear flow of data from the user interface to external services and back. The design emphasizes separation of concerns, allowing each module to handle a specific responsibility while keeping the overall system simple to test and extend.

---

## High-Level Flow (tied to flowchart)

1. **User Interface (UI)**  
   - The entry point for user interaction.  
   - Implemented through a web client (e.g., Gradio, HTML templates, or API endpoint).  
   - Captures user input and displays bot responses.

2. **Router / Core Logic**  
   - Handles conversation state and routes messages.  
   - Delegates to either the anonymous bot, logged-in bot, or agentic extensions.  
   - Imports lightweight rules from `anon_bot/rules.py` for anonymous sessions, and integrates with advanced providers for logged-in sessions.

3. **NLU (Natural Language Understanding)**  
   - Managed by the `nlu/` pipeline (intent recognition, prompts, and routing).  
   - Provides preprocessing, normalization, and optional summarization/RAG.  
   - Keeps the system extensible for additional models without changing the rest of the stack.

4. **Memory & Context Layer**  
   - Implemented in `memory/` (sessions, store, and optional RAG retriever/indexer).  
   - Stores session history, enabling context-aware responses.  
   - Supports modular backends (in-memory, file-based, or vector index).

5. **External AI Service Connector (optional)**  
   - For logged-in flows, integrates with cloud AIaaS (e.g., Azure, HuggingFace, or open-source LLMs).  
   - Uses `logged_in_bot/sentiment_azure.py` or `agenticcore/providers_unified.py`.  
   - Provides NLP services like sentiment analysis or summarization.  
   - Disabled in anonymous mode for privacy.

6. **Guardrails & Safety**  
   - Defined in `guardrails/` (PII redaction, safety filters).  
   - Applied before responses are shown to the user.  
   - Ensures compliance with privacy/security requirements.

7. **Outputs**  
   - Bot response returned to the UI.  
   - Logs written via `core/logging.py` for traceability and debugging.  
   - Optional screenshots and reports recorded for evaluation.

---

## Key Principles

- **Modularity**: Each part of the flow is a self-contained module (UI, NLU, memory, guardrails).  
- **Swap-in Providers**: Agentic core can switch between local rules, RAG memory, or external APIs.  
- **Anonymous vs Logged-In**: Anonymous bot uses lightweight rules with no external calls; logged-in bot can call providers.  
- **Extensibility**: Flowchart design makes it easy to add summarization, conversation modes, or other “agentic” behaviors without rewriting the core.  
- **Resilience**: If an external service fails, the system degrades gracefully to local responses.

---

## Mapping to Repo Structure

- `app/` → User-facing entrypoint (routes, HTML, API).  
- `anon_bot/` → Anonymous chatbot rules + handler.  
- `logged_in_bot/` → Provider-based flows for authenticated users.  
- `nlu/` → Intent routing, prompts, pipeline.  
- `memory/` → Session management + RAG integration.  
- `guardrails/` → Safety filters + PII redaction.  
- `agenticcore/` → Core integration logic and unified providers.  
- `docs/flowchart.png` → Visual representation of this architecture.

---

## Summary

The architecture ensures a **clean separation between interface, logic, and services**, enabling experimentation with different providers while guaranteeing a safe, privacy-friendly anonymous mode. The flowchart illustrates this layered approach: input → logic → NLU/memory → optional AIaaS → guardrails → output.

## Documentation

- [Brief Academic Write Up](Brief_Academic_Write_Up.md)
- [README](../README.md)
- [Architecture Overview](architecture.md)  
- [Design Notes](design.md) 
- [Developer & Build/Test Guide](Developer_Guide_Build_Test.md) 
- [Implementation Notes](storefront/IMPLEMENTATION.md) 
- [Dev Doc](DEV_DOC.md)  
- [Developer Guide Build Test](Developer_Guide_Build_Test.md) 