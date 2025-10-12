# Logged-In Bot Module

Quick reference for the logged-in bot functionality.

## Quick Start

```python
from logged_in_bot import handle_logged_in_turn

# Process a user message
response = handle_logged_in_turn(
    message="I love this chatbot!",
    history=[],  # List of (user, bot) tuples
    user={"id": "user_123", "name": "Anish"}
)

print(response["reply"])
print(response["meta"]["sentiment"])
```

## API Reference

### Main Entry Point

```python
def handle_logged_in_turn(
    message: str,
    history: Optional[List[Tuple[str, str]]],
    user: Optional[dict]
) -> Dict[str, Any]
```

**Returns**:
```python
{
    "reply": str,           # Bot response
    "meta": {
        "intent": str,      # Detected intent
        "redacted": bool,   # Whether PII was redacted
        "input_len": int,   # Input length
        "sentiment": {
            "label": str,   # "positive" | "neutral" | "negative"
            "score": float, # 0.0 to 1.0
            "backend": str  # "azure" | "local" | "hf"
        }
    }
}
```

### Supported Commands

| Command | Example | Description |
|---------|---------|-------------|
| `help` | `help` | Show capabilities |
| `echo` | `echo Hello World` | Echo back text |
| `summarize` | `summarize Long text here...` | Extract first sentence |
| `remember` | `remember name: Anish` | Store user preference |
| `forget` | `forget name` | Remove preference |
| `list memory` | `list memory` | Show all stored keys |
| General chat | `What is RAG?` | RAG-based response |

### Utility Functions

```python
# Get system capabilities
capabilities() -> List[str]

# Redact PII from text
redact_text(text: str) -> str

# Detect intent
intent_of(text: str) -> str

# Summarize text
summarize_text(text: str, target_len: int = 120) -> str
```

### Sentiment Analysis

```python
from logged_in_bot.sentiment_azure import analyze_sentiment

result = analyze_sentiment("I love this!")
print(result.label)    # "positive"
print(result.score)    # 0.8
print(result.backend)  # "local" or "azure"
```

## Environment Setup

```bash
# Optional: Hugging Face (recommended)
export HF_API_KEY=your_key_here
export HF_MODEL_SENTIMENT=distilbert/distilbert-base-uncased-finetuned-sst-2-english

# Optional: Azure Text Analytics
export AZURE_LANGUAGE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
export AZURE_LANGUAGE_KEY=your_key_here

# Feature toggles
export SENTIMENT_ENABLED=true
export MAX_INPUT_CHARS=4000
```

## Integration Examples

### With Gradio

```python
import gradio as gr
from logged_in_bot import handle_logged_in_turn

def chat(message, history):
    user = {"id": "demo_user", "name": "Demo"}
    response = handle_logged_in_turn(message, history, user)
    return response["reply"]

gr.ChatInterface(chat).launch()
```

### With FastAPI

```python
from fastapi import FastAPI
from logged_in_bot import handle_logged_in_turn

app = FastAPI()

@app.post("/chat")
async def chat(message: str, user_id: str):
    response = handle_logged_in_turn(
        message=message,
        history=[],
        user={"id": user_id}
    )
    return response
```

### With Session Memory

```python
from logged_in_bot import handle_logged_in_turn
from memory.sessions import SessionStore

store = SessionStore()
session = store.create(user_id="user_123")

# Process message
response = handle_logged_in_turn(
    message="Hello!",
    history=session.history,
    user={"id": "user_123"}
)

# Save to session
store.append_user(session.session_id, "Hello!")
store.append_bot(session.session_id, response["reply"])
```

## Testing

```bash
# Run all tests
pytest tests/test_logged_in_bot.py -v

# Run specific test
pytest tests/test_logged_in_bot.py::test_help_route_and_reply -v

# Run with coverage
pytest tests/test_logged_in_bot.py --cov=logged_in_bot
```

## Architecture

```
logged_in_bot/
├── __init__.py           # Module exports
├── handler.py            # ChatBot integration
├── tools.py              # Main logic & routing
├── sentiment_azure.py    # Sentiment analysis
└── README.md            # This file

Dependencies:
├── nlu/                 # Intent classification & routing
├── memory/              # Session & profile storage
├── guardrails/          # PII redaction
└── agenticcore/         # Provider integrations
```

## Troubleshooting

### No sentiment detected
- Check `HF_API_KEY` or `AZURE_LANGUAGE_KEY` is set
- Verify API endpoint is accessible
- Falls back to local heuristic automatically

### PII not redacted
- Ensure `guardrails.pii_redaction` is installed
- Check patterns in `guardrails/pii_redaction.py`
- Redaction is optional and fails open

### Memory not persisting
- Check `memory/.profiles/` directory exists
- Verify write permissions
- Use `Profile.save()` explicitly if needed

### RAG returns no results
- Index documents first: `python -m memory.rag.indexer`
- Check `memory/rag/data/` has indexed files
- Verify query matches document content

## Performance Tips

1. **Cache sentiment results** for repeated queries
2. **Limit history length** to last 50-100 turns
3. **Use local sentiment** for high-throughput scenarios
4. **Batch API calls** when processing multiple messages
5. **Pre-index documents** before deployment

## Security Notes

- PII redaction is best-effort, not guaranteed
- Validate user input before processing
- Sanitize output before displaying to users
- Use HTTPS for API calls
- Rotate API keys regularly
- Monitor for abuse patterns

## Contributing

When adding features:
1. Update `capabilities()` list
2. Add intent to `intent_of()`
3. Implement handler in `handle_logged_in_turn()`
4. Add tests to `test_logged_in_bot.py`
5. Update this README

## License

See [LICENSE](../LICENSE) in project root.

## Support

For issues or questions:
- Check [Developer Guide](../docs/Developer_Guide_Build_Test.md)
- Review [test cases](../tests/test_logged_in_bot.py)
- See [main README](../README.md)

---

**Owner**: Anish Thakur  
**Version**: 1.0.0  
**Status**: Production Ready ✅
