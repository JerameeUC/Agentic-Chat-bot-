<!-- /docs/DEV_DOC.md -->
## 3. Functional Requirements

This section describes the functional requirements for connecting a chatbot to an AI-as-a-Service (AIaaS) platform. It defines the expected system behavior, outlines constraints, and sets measurable acceptance criteria. Requirements are grouped into system context, core functions, supporting functions, and non-functional aspects.

---

### 3.1 System Context

The chatbot acts as the client application. It receives user input, processes it, and communicates with an external AIaaS endpoint (e.g., Azure AI Language Service). The AI service provides natural language processing (NLP) features such as sentiment analysis. The chatbot then interprets the service output and responds back to the user.

Key components include:
- **User Interface (UI):** Chat interface for entering text.
- **Chatbot Core:** Handles request routing and conversation logic.
- **AI Service Connector:** Manages authentication and API calls to the AI service.
- **AIaaS Platform:** External cloud service providing NLP functions.

---

### 3.2 Functional Requirements

#### FR-1: User Input Handling
- The chatbot shall accept text input from users.
- The chatbot shall sanitize input to remove unsafe characters.
- The chatbot shall log all interactions for debugging and testing.

#### FR-2: API Connection
- The system shall authenticate with the AI service using API keys stored securely in environment variables.
- The chatbot shall send user text to the AIaaS endpoint in the required format.
- The chatbot shall handle and parse responses from the AIaaS.

#### FR-3: Sentiment Analysis Integration
- The chatbot shall use the AIaaS to determine the sentiment (e.g., positive, neutral, negative) of user input.
- The chatbot shall present sentiment results as part of its response or use them to adjust tone.

#### FR-4: Error and Exception Handling
- The system shall detect failed API calls and return a fallback message to the user.
- The chatbot shall notify the user if the AI service is unavailable.
- The chatbot shall log errors with timestamp and cause.

#### FR-5: Reporting and Documentation
- The chatbot shall provide a list of supported commands or features when prompted.
- The chatbot shall record system status and output for inclusion in the project report.
- The development process shall be documented with screenshots and configuration notes.

---

### 3.3 Non-Functional Requirements

#### NFR-1: Security
- API keys shall not be hard-coded in source files.
- Sensitive data shall be retrieved from environment variables or secure vaults.

#### NFR-2: Performance
- The chatbot shall return responses within 2 seconds under normal network conditions.
- The system shall process at least 20 concurrent user sessions without performance degradation.

#### NFR-3: Reliability
- The chatbot shall achieve at least 95% uptime during testing.
- The chatbot shall gracefully degrade to local responses if the AI service is unavailable.

#### NFR-4: Usability
- The chatbot shall provide clear, user-friendly error messages.
- The chatbot shall handle malformed input without crashing.

---

### 3.4 Acceptance Criteria

1. **Input Handling**
   - Given valid text input, the chatbot processes it without errors.
   - Given invalid or malformed input, the chatbot responds with a clarification request.

2. **API Connection**
   - Given a valid API key and endpoint, the chatbot connects and retrieves sentiment analysis.
   - Given an invalid API key, the chatbot logs an error and informs the user.

3. **Sentiment Analysis**
   - Given a positive statement, the chatbot labels it correctly with at least 90% accuracy.
   - Given a negative statement, the chatbot labels it correctly with at least 90% accuracy.

4. **Error Handling**
   - When the AI service is unavailable, the chatbot informs the user and continues functioning with local responses.
   - All failures are recorded in a log file.

5. **Usability**
   - The chatbot returns responses in less than 2 seconds for 95% of requests.
   - The chatbot displays a list of features when the user requests “help.”

---

### Glossary

- **AIaaS (AI-as-a-Service):** Cloud-based artificial intelligence services accessible via APIs.
- **API (Application Programming Interface):** A set of rules for software applications to communicate with each other.
- **NLP (Natural Language Processing):** A field of AI focused on enabling computers to understand human language.
- **Sentiment Analysis:** An NLP technique that determines the emotional tone behind a text.

## Documentation

- [Brief Academic Write Up](docs/Brief_Academic_Write_Up.md)
- [README](../README.md)
- [Architecture Overview](architecture.md)  
- [Design Notes](design.md)  
- [Implementation Notes](storefront/IMPLEMENTATION.md) 
- [Dev Doc](DEV_DOC.md)
- [Developer Guide Build Test](Developer_Guide_Build_Test.md) 
