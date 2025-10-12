# Conversational RAG Implementation

## Overview

The chatbot now provides **natural, conversational responses** instead of just returning raw document chunks. It combines:

1. **RAG (Retrieval-Augmented Generation)**: Retrieves relevant information from indexed documents
2. **Conversational AI**: Generates natural responses using context and chat history
3. **Memory**: Remembers user preferences and conversation context
4. **Intent Routing**: Switches between conversation, summarization, and retrieval

## Key Features

### ✅ Natural Conversation
Instead of dumping document text, the bot extracts key information and responds naturally:

**Before (Document Dump)**:
```
User: Can I buy parking passes?
Bot: GRADUATION STORE - PRODUCT CATALOG AVAILABLE PRODUCTS: 1. Cap and Gown Set...
```

**After (Conversational)**:
```
User: Can I buy parking passes?
Bot: Yes! You can buy as many parking passes as you need. There's no limit - perfect 
     for extended families. Each pass is for one vehicle.
```

### ✅ Context Awareness
The bot understands follow-up questions by tracking conversation history:

```
User: Can I buy parking passes?
Bot: Yes! You can buy as many parking passes as you need...

User: How many can I buy?
Bot: You can buy as many as you need! There's no limit on parking passes...
```

### ✅ Personalization
Uses stored user information to personalize responses:

```
User: remember name: Alice
Bot: Okay, I'll remember **name**.

User: Hi!
Bot: Hi Alice! I can help you with graduation store questions. What would you like to know?
```

### ✅ RAG Grounding
All responses are grounded in indexed documents - no hallucination:

```
User: What's the dress code?
Bot: For the dress code: formal attire is recommended but not required for guests. 
     However, muscle shirts and sagging pants are not allowed in the venue.
```

## Architecture

### Response Generation Flow

```
User Query
    ↓
Intent Detection (help | memory | summarize | chat)
    ↓
[If chat intent]
    ↓
Retrieve User Profile (name, preferences)
    ↓
Get Chat History (last 4 turns)
    ↓
RAG Retrieval (TF-IDF + proximity reranking)
    ↓
Key Info Extraction (query + context aware)
    ↓
Conversational Response Generation
    ↓
Natural Language Response
```

### Components

1. **`_retrieve_context()`**: TF-IDF retrieval with confidence scoring
2. **`_extract_key_info()`**: Extracts structured answers from documents based on query + context
3. **`_format_rag_response()`**: Formats document chunks into readable responses
4. **`_generate_conversational_response()`**: Orchestrates the full response generation

### LLM Integration

The system supports multiple LLM providers (via `agenticcore/providers_unified.py`):
- OpenAI (GPT-3.5/4)
- Hugging Face
- Cohere
- Azure
- **Offline fallback** (rule-based extraction)

When an LLM is available, it generates natural responses. Otherwise, the system uses intelligent rule-based extraction.

## Example Conversations

### Graduation Store Questions

```
User: Can I buy parking passes?
Bot: Yes! You can buy as many parking passes as you need. There's no limit - 
     perfect for extended families. Each pass is for one vehicle.

User: How many can I buy?
Bot: You can buy as many as you need! There's no limit on parking passes - 
     perfect for extended families. Each pass is for one vehicle.

User: What about handicap parking?
Bot: Important: vehicles parked in handicap spaces without proper permits will 
     be towed immediately. Also, no double parking is allowed.
```

### Dress Code Questions

```
User: What's the dress code?
Bot: For the dress code: formal attire is recommended but not required for guests. 
     However, muscle shirts and sagging pants are not allowed in the venue.

User: Are muscle shirts allowed?
Bot: No, muscle shirts are not allowed in the venue. The dress code requires 
     appropriate attire - formal is recommended but business casual is acceptable.
```

### Memory Commands

```
User: remember name: Bob
Bot: Okay, I'll remember **name**.

User: remember favorite_color: blue
Bot: Okay, I'll remember **favorite_color**.

User: list memory
Bot: Saved keys: favorite_color, name
```

## Configuration

### Environment Variables

```bash
# LLM Provider (optional - falls back to offline mode)
AI_PROVIDER=openai  # or hf, azure, cohere, deepai, offline
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# Or use Hugging Face
HF_API_KEY=hf_...
HF_MODEL_GENERATION=tiiuae/falcon-7b-instruct
```

### Confidence Thresholds

Adjust in `logged_in_bot/tools.py`:

```python
# High confidence: direct, confident answers
if confidence >= 25:
    # "Yes! You can buy..."

# Medium confidence: softer phrasing  
elif confidence >= 14:
    # "Based on the documents..."

# Low confidence: acknowledge uncertainty
else:
    # "I'm not entirely sure, but..."
```

## Testing

```bash
cd /home/anish/PycharmProjects/Agentic-Chat-bot-
source .venv/bin/activate

python3 << 'EOF'
from logged_in_bot.tools import handle_logged_in_turn

user = {"id": "test_user"}
history = []

# Test conversation
messages = [
    "remember name: Alice",
    "Hi!",
    "Can I buy parking passes?",
    "How many can I buy?",
]

for msg in messages:
    result = handle_logged_in_turn(msg, history, user)
    print(f"User: {msg}")
    print(f"Bot: {result['reply']}\n")
    history.append(("user", msg))
    history.append(("bot", result['reply']))
EOF
```

## Alignment with Project Objectives

| Objective | Implementation | Status |
|-----------|----------------|--------|
| **Switch between conversation, summarization, and retrieval** | Intent router handles: help, memory, summarize, echo, chat (RAG) | ✅ Complete |
| **Use RAG to ground answers in curated data** | TF-IDF retrieval + conversational extraction | ✅ Complete |
| **Demonstrate memory** | User profile (name, preferences) + chat history | ✅ Complete |
| **Scrape document headers** | TF-IDF indexer extracts metadata (title, tags) | ✅ Complete |
| **Respect data privacy** | Session-bound memory, optional PII redaction | ✅ Complete |

## Future Enhancements

1. **Better LLM Integration**: Add more sophisticated prompts for nuanced responses
2. **Multi-turn Dialogue**: Track conversation topics across multiple turns
3. **Clarification Questions**: Ask users for clarification when queries are ambiguous
4. **Sentiment-Aware Responses**: Adjust tone based on user sentiment
5. **Proactive Suggestions**: Suggest related questions based on current topic

## References

- RAG: [Lewis et al., 2020](https://arxiv.org/abs/2005.11401)
- Conversational AI: [Gao et al., 2019](https://arxiv.org/abs/1809.08267)
- Context-Aware Dialogue: [Zhang et al., 2020](https://arxiv.org/abs/1911.03768)
