# SRS Traceability Matrix
**Project:** Storefront Chatbot  
**Version:** 1.0  
**Location:** `docs/SRS_Traceability.md`  
**Purpose:** Tracks requirements, ownership, and verification status for all major modules.

---

## 1. Functional Requirements

| Req ID | Description | Module | Owner | Priority | Verification | Status |
|--------|--------------|---------|--------|-----------|---------------|---------|
| FR-1.1 | Reject disallowed content (violence, weapons). | guardrails.py | C | High | Unit Test | ✅ |
| FR-1.2 | Redact PII before display/storage. | guardrails.py | C | High | Unit Test | ✅ |
| FR-1.3 | Replace profane words with `[REDACTED]`. | guardrails.py | C | Medium | Unit Test | ✅ |
| FR-1.4 | Apply guardrails before routing. | anon_bot/handler.py | C | High | Integration | ⚙️ |
| FR-2.1 | Process messages via `/message` statelessly. | anon_bot/handler.py | C | High | Manual QA | ⚙️ |
| FR-2.2 | Deterministic rule-based responses. | anon_bot/handler.py | C | Medium | Manual QA | ⚙️ |
| FR-2.3 | No logging of raw inputs. | anon_bot/handler.py | C | High | Audit Review | ⚙️ |
| FR-3.1 | Use HF pipeline for intent/entity extraction. | nlu/pipeline.py | B | High | Unit Test | ✅ |
| FR-3.2 | Integrate Azure sentiment (optional). | sentiment_azure.py | B | Medium | Integration | ⚙️ |
| FR-3.3 | Return reply + sentiment/confidence. | logged_in_bot/handler.py | B | High | Unit Test | ✅ |
| FR-3.4 | Handle runtime errors gracefully. | logged_in_bot/handler.py | B | High | Unit Test | ✅ |
| FR-3.5 | Route message intents to correct domain. | nlu/router.py | B | High | Unit Test | ✅ |
| FR-4.1 | Create user sessions with TTL. | memory/sessions.py | D | High | Unit Test | ✅ |
| FR-4.2 | Maintain capped session history. | memory/sessions.py | D | Medium | Unit Test | ✅ |
| FR-4.3 | Allow user notes with consent. | memory/profile.py | D | Medium | Unit Test | ✅ |
| FR-4.4 | Persist user profiles to JSON. | memory/profile.py | D | Medium | Integration | ✅ |
| FR-4.5 | Save/load sessions for recovery. | memory/sessions.py | D | Medium | Unit Test | ✅ |
| FR-5.1 | Build TF-IDF index and tokenize text. | memory/rag/indexer.py | D | High | Unit Test | ✅ |
| FR-5.2 | Retrieve top-k passages by proximity. | memory/rag/retriever.py | D | High | Integration | ⚙️ |
| FR-5.3 | Filter retrievals by title/tags. | memory/rag/retriever.py | D | Low | Integration | ⚙️ |
| FR-5.4 | Return structured retrieval results. | memory/rag/retriever.py | D | Medium | Unit Test | ✅ |

---

## 2. Non-Functional Requirements

| Req ID | Description | Category | Owner | Verification | Status |
|--------|--------------|-----------|--------|--------------|---------|
| NFR-1 | Response time < 2 s average. | Performance | All | Load Test | ⚙️ |
| NFR-2 | Fallback prevents crashes. | Reliability | B/D | Unit Test | ✅ |
| NFR-3 | PII redaction enforced. | Security | C/D | Unit Test | ✅ |
| NFR-4 | Run locally or in Hugging Face Space. | Portability | All | Demo Run | ✅ |
| NFR-5 | Handle 5+ concurrent users. | Scalability | All | Load Test | ⚙️ |
| NFR-6 | Modular, no circular imports. | Maintainability | All | Code Review | ✅ |
| NFR-7 | HIPAA/PII best-effort compliance. | Compliance | E | Documentation | ✅ |

---

## 3. Verification Legend

| Symbol | Meaning |
|---------|----------|
| ✅ | Verified / Completed |
| ⚙️ | Pending Integration or QA |
| ⛔ | Blocked or Not Started |

---

## 4. Notes

- Owner **B (Anish)** oversees NLU and sentiment integration testing.  
- Owner **C (Aziz)** manages guardrails and anon flow validation.  
- Owner **D (Jeramee)** owns persistence and retrieval subsystems.  
- Owner **E (Rahul)** ensures CI and documentation alignment across the repo.  

---

*Document Version 1.0 — Last Updated: October 2025*
