# LLM Fallback for General Knowledge ✅

## Overview

The chatbot now intelligently routes questions:
- **Document-related questions** → RAG (retrieves from indexed documents)
- **General knowledge questions** → LLM (uses language model to answer)

## How It Works

### 1. Keyword Detection

The system checks if the query is about indexed documents using word-boundary matching:

```python
doc_keywords = [
    'parking', 'dress', 'attire', 'cap and gown', 'gown', 'product',
    'buy', 'purchase', 'graduation', 'ceremony', 'store', 'pass',
    'rule', 'wear', 'shirt', 'pants', 'venue', 'handicap', 'tow',
    'muscle', 'sagging', 'formal', 'tassel'
]
```

### 2. Routing Logic

```
Query received
    ↓
Check if about documents (keyword match)
    ↓
YES → Use RAG (retrieve from documents)
    ↓
NO → Use LLM (general knowledge)
```

## Examples

### Document Questions (Use RAG)

```
User: What products can I buy?
Bot: We offer: 1) Cap and Gown Set (includes cap, gown, tassel - required 
     for ceremony), and 2) Parking Passes (valid for graduation day, no 
     limit per student).

User: What are the parking rules?
Bot: Parking rules: No double parking is allowed at any time. Vehicles 
     parked in handicap spaces without proper permits will be towed 
     immediately. Arrive early for best availability.
```

### General Knowledge (Use LLM)

```
User: What is the capital of Nepal?
Bot: I don't have that in my documents, but here's what I know: The capital 
     of Nepal is Kathmandu.

User: Who invented the telephone?
Bot: I don't have that in my documents, but here's what I know: Alexander 
     Graham Bell is credited with inventing the telephone in 1876.
```

### When LLM is Offline

```
User: What is the capital of Nepal?
Bot: I don't have information about that in my documents. I can help with 
     questions about the graduation store (products, parking, dress code). 
     You can also upload documents for me to reference.
```

## Configuration

### Enable LLM

Set environment variables in `.env`:

```bash
# Option 1: OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# Option 2: Hugging Face
HF_API_KEY=hf_...
HF_MODEL_GENERATION=tiiuae/falcon-7b-instruct

# Option 3: Local LLM
USE_LOCAL_LLM=true
LOCAL_LLM_MODEL=microsoft/phi-2
```

### Without LLM

The system works fine without an LLM - it will:
1. Answer document-related questions using RAG
2. Provide helpful guidance for general knowledge questions

## Technical Implementation

### Key Fix: Word Boundaries

**Problem:** "capital" was matching "cap" keyword, causing general knowledge questions to use RAG.

**Solution:** Use regex word boundaries (`\b`):

```python
# Before (substring match)
'cap' in 'capital'  # True ❌

# After (word boundary)
re.search(r'\bcap\b', 'capital')  # None ✅
re.search(r'\bcap\b', 'cap and gown')  # Match ✅
```

### Response Flow

```python
def _generate_conversational_response(...):
    # 1. Check if about documents
    is_about_docs = any(regex.search(pattern, query_lower) 
                       for pattern in doc_keywords)
    
    # 2. Use RAG if about documents
    if rag_chunks and is_about_docs:
        return format_rag_response(...)
    
    # 3. Try LLM for general knowledge
    llm_result = generate_text(query)
    if llm_available:
        return f"I don't have that in my documents, but here's what I know: {llm_text}"
    
    # 4. Fallback message
    return "I don't have information about that..."
```

## Benefits

1. ✅ **Accurate routing** - Document questions use RAG, general knowledge uses LLM
2. ✅ **No false matches** - Word boundaries prevent "capital" matching "cap"
3. ✅ **Graceful degradation** - Works without LLM (provides helpful message)
4. ✅ **Transparent** - Tells users when answering from documents vs general knowledge
5. ✅ **Extensible** - Easy to add more document keywords

## Testing

```bash
python3 << 'EOF'
from logged_in_bot.tools import handle_logged_in_turn

user = {"id": "test", "name": "test"}

# Document question
result = handle_logged_in_turn("What products can I buy?", [], user)
# → Uses RAG

# General knowledge
result = handle_logged_in_turn("What is the capital of Nepal?", [], user)
# → Uses LLM (or helpful message if offline)
EOF
```

## Summary

The chatbot now intelligently routes questions:
- **Document questions** → RAG retrieval
- **General knowledge** → LLM (with graceful fallback)

This provides the best of both worlds: grounded answers for document questions, and helpful responses for general knowledge! 🚀
