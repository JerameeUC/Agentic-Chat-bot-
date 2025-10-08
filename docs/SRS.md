# Software Requirements Specification (SRS)
**Project:** Storefront Chatbot  
**Version:** 1.0  
**Location:** `docs/SRS.md`  
**Authors:**  
- Owner A – Frontend/UI: Rojina Sunuwar  
- Owner B – Logged-in Bot & NLU: Anish Thakur  
- Owner C – Anonymous Bot & Guardrails: Volunteer  
- Owner D – Memory & RAG: Jeramee Oliver  
- Owner E – Documentation, CI, Compliance: Volunteer  

---

## 1. Introduction

### 1.1 Purpose
This document defines the functional and non-functional requirements of the **Storefront Chatbot** system.  
It aligns project members (Owners A–E) on architecture, interfaces, and compliance expectations.  
The chatbot enables users to interact with a simulated storefront through either **anonymous** or **logged-in** modes, using **Gradio** for the front-end and **FastAPI** for backend services.

### 1.2 Scope
The chatbot supports:
- Anonymous browsing and FAQs without persistence.  
- Logged-in sessions with persistent memory and optional Azure sentiment analysis.  
- Lightweight Retrieval-Augmented Generation (RAG) over product/FAQ snippets.  
- Guardrails for PII redaction, profanity filtering, and topic restrictions.  
- Configurable toggles for external connectors (Azure, Redis, PostgreSQL).

### 1.3 References
- `docs/architecture.md`, `docs/design.md`, `DEV_DOC.md`  
- IEEE 830, ISO 29148 (software requirements)  
- Hugging Face Transformers, Gradio, FastAPI, Azure Text Analytics SDK  

---

## 2. Overall Description

### 2.1 Product Perspective
The chatbot functions as a modular web app:
- **Frontend/UI:** Gradio Blocks (`app/app.py`)
- **Back-End Services:** FastAPI endpoints for message routing
- **Core Intelligence:** Hugging Face NLU + rule-based logic
- **Persistence Layer:** Session store and profile memory
- **Retrieval Engine:** TF-IDF based RAG index
- **Guardrails Layer:** Regex-based text safety and redaction

### 2.2 User Classes and Characteristics
| User Type | Description | Persistence |
|------------|--------------|-------------|
| Anonymous User | Public visitor, no login, stateless | ❌ |
| Logged-in User | Identified session, personalized responses | ✅ |
| Developer / Maintainer | Internal contributor, test/extend modules | N/A |

### 2.3 Constraints
- No sensitive PII stored in logs.  
- Azure connectors optional; system must degrade gracefully if disabled.  
- All sessions auto-expire after TTL (default: 3600 s).  
- RAG index limited to lightweight, on-disk TF-IDF implementation (no heavy GPU inference).

---

## 3. System Architecture Overview

```text
User → Guardrails → (NLU + Intent Router) → Bot Handler
         ↳ Anonymous Path → Rule-based reply
         ↳ Logged-in Path → Memory + Sentiment + RAG
```

- **Anon Bot:** Stateless request–reply, uses guardrails before routing.  
- **Logged-in Bot:** Manages context and sentiment through Hugging Face or Azure.  
- **Memory Layer:** SessionStore, Profile, and RAG modules store and recall data.  
- **Guardrails:** Pre-validation and redaction of unsafe content.

---

## 4. Functional Requirements

### 4.1 Guardrails (Owner C)
| ID | Requirement | Source |
|----|--------------|--------|
| FR-1.1 | System shall reject messages containing disallowed patterns (weapons, violence). | `guardrails.py` |
| FR-1.2 | System shall redact PII (emails, phone numbers) before storage or display. | `guardrails.py` |
| FR-1.3 | System shall replace profane words with `[REDACTED]`. | `guardrails.py` |
| FR-1.4 | Guardrail enforcement shall precede all NLU or rule routing calls. | `anon_bot/handler.py` |

### 4.2 Anonymous Bot (Owner C)
| ID | Requirement | Source |
|----|--------------|--------|
| FR-2.1 | System shall process requests through `/message` without requiring a session ID. | `anon_bot/handler.py` |
| FR-2.2 | Responses shall be deterministic and rule-based using `rules.route()`. | `anon_bot/handler.py` |
| FR-2.3 | No raw input shall be logged or stored. | Design Doc |

### 4.3 NLU + Logged-in Bot (Owner B)
| ID | Requirement | Source |
|----|--------------|--------|
| FR-3.1 | NLU shall use Hugging Face pipelines for intent, entity, and summarization. | `nlu/pipeline.py` |
| FR-3.2 | Sentiment module shall call Azure Text Analytics when enabled. | `sentiment_azure.py` |
| FR-3.3 | Logged-in handler shall return chatbot reply and optional sentiment/confidence. | `logged_in_bot/handler.py` |
| FR-3.4 | Fallback message displayed on errors. | `logged_in_bot/handler.py` |
| FR-3.5 | Intent router shall direct messages to appropriate domain (shop/order/general). | `nlu/router.py` |

### 4.4 Memory & Profile (Owner D)
| ID | Requirement | Source |
|----|--------------|--------|
| FR-4.1 | System shall create session with UUID and TTL on login. | `memory/sessions.py` |
| FR-4.2 | Session shall store user/bot history, trimmed to max length. | `memory/sessions.py` |
| FR-4.3 | Users may store personal notes with explicit consent. | `memory/profile.py` |
| FR-4.4 | Profiles shall persist in JSON files within `memory/.profiles`. | `memory/profile.py` |
| FR-4.5 | SessionStore shall support JSON save/load for recovery. | `memory/sessions.py` |

### 4.5 RAG & Retrieval (Owner D)
| ID | Requirement | Source |
|----|--------------|--------|
| FR-5.1 | TF-IDF index shall tokenize, count terms, and store document metadata. | `memory/rag/indexer.py` |
| FR-5.2 | Retriever shall return top-k passages with reranking by token proximity. | `memory/rag/retriever.py` |
| FR-5.3 | Optional filters shall restrict results by title substring or tags. | `memory/rag/retriever.py` |
| FR-5.4 | Retrieval output shall include doc_id, source, title, score, and snippet. | `retriever.py` |

---

## 5. Interface Requirements

### 5.1 Inter-Module Interfaces
```text
(1) Guardrails.enforce_guardrails()
    → returns (ok:bool, text:str)
(2) NLU.pipeline.infer()
    → returns intent, entities, summary
(3) LoggedInBot.handle_turn()
    → returns history[[user,bot]]
(4) Memory.SessionStore
    → create(), get(), append_user(), append_bot()
(5) RAG.retrieve(query)
    → returns List[Passage]
```

### 5.2 Data Flow Summary
**Anonymous:**  
`User → Guardrails → Rules Router → Reply`

**Logged-in:**  
`User → Guardrails → NLU → Sentiment → Session Memory → RAG → Reply`

---

## 6. Data Management

### 6.1 Session Data
Stored transiently in memory; expires after TTL.  
```json
{
  "session_id": "uuid4",
  "user_id": "abc123",
  "history": [["user","hi"],["bot","hello"]],
  "data": {"cart_items":3}
}
```

### 6.2 Profile Data
User-controlled, opt-in persistence in `memory/.profiles`.

### 6.3 RAG Index
Documents serialized to JSON via `indexer.save()`.  
Supports reload and keyword search; does not store PII.

---

## 7. Non-Functional Requirements

| ID | Category | Description |
|----|-----------|-------------|
| NFR-1 | Performance | Average response time < 2 s for queries. |
| NFR-2 | Reliability | Fallback responses prevent crashes. |
| NFR-3 | Security | PII and profanity redaction required for all inputs. |
| NFR-4 | Portability | Compatible with local or Hugging Face Spaces runtime. |
| NFR-5 | Scalability | Must handle 5 concurrent user sessions in demo mode. |
| NFR-6 | Maintainability | Modular file structure; no circular imports. |
| NFR-7 | Compliance | HIPAA/PII guidelines followed on best-effort basis (non-binding). |

---

## 8. Privacy, Safety & Compliance

- **PII Redaction:** Emails and phone numbers are scrubbed before processing.  
- **No Persistent Logs:** Anonymous path retains no input data.  
- **Opt-In Memory:** Logged-in profiles saved only with explicit consent.  
- **Ethical Guardrails:** System refuses unsafe topics (weapons, violence).  
- **HIPAA Consideration:** Non-binding compliance — no medical data processed.

---

## 9. Traceability Summary (Preview)

| Req ID | Module | Owner | Verified By |
|---------|---------|--------|-------------|
| FR-1.1–1.4 | `guardrails.py` | C | Unit test |
| FR-2.1–2.3 | `anon_bot/handler.py` | C | Manual QA |
| FR-3.1–3.5 | `nlu/`, `logged_in_bot/` | B | Unit + Integration |
| FR-4.1–4.5 | `memory/sessions.py`, `profile.py` | D | Unit test |
| FR-5.1–5.4 | `memory/rag/` | D | Integration test |
| NFR-1–NFR-7 | Cross-cutting | All | Observation |

---

## 10. Appendix

### 10.1 Tools & Dependencies
- **Python 3.11+**, **Gradio**, **FastAPI**, **transformers**, **openai/azure SDKs**  
- **pytest** for unit testing, **Makefile** for automation

### 10.2 Future Enhancements
- Multi-user DB-backed persistence (PostgreSQL)
- LLM-based summarization and FAQ enrichment
- UI enhancements (user avatars, order tracking)

---

*End of Document*
