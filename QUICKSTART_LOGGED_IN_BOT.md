# 🚀 Quick Start: Logged-In Bot

Get started with the logged-in bot in 5 minutes!

## 1️⃣ Verify Installation

```bash
cd /home/anish/PycharmProjects/Agentic-Chat-bot-
python tools/validate_logged_in_bot.py
```

Expected output: `🎉 All validation tests passed!`

## 2️⃣ Basic Usage

```python
from logged_in_bot import handle_logged_in_turn

# Define user
user = {"id": "user_123", "name": "Anish"}

# Send message
response = handle_logged_in_turn("help", [], user)

# Get reply
print(response["reply"])
# Output: I can:
#         - help
#         - remember <key>: <value>
#         - forget <key>
#         - list memory
#         - echo <text>
#         - summarize <paragraph>
#         - sentiment tagging (logged-in mode)
```

## 3️⃣ Try Different Commands

### Echo
```python
response = handle_logged_in_turn("echo Hello World", [], user)
print(response["reply"])
# Output: Hello World
```

### Summarize
```python
response = handle_logged_in_turn(
    "summarize This is the first sentence. This is the second sentence.",
    [],
    user
)
print(response["reply"])
# Output: This is the first sentence.
```

### Memory
```python
# Remember
response = handle_logged_in_turn("remember favorite_color: blue", [], user)
print(response["reply"])
# Output: Okay, I'll remember **favorite_color**.

# List
response = handle_logged_in_turn("list memory", [], user)
print(response["reply"])
# Output: Saved keys: favorite_color

# Forget
response = handle_logged_in_turn("forget favorite_color", [], user)
print(response["reply"])
# Output: Forgot.
```

### Sentiment Analysis
```python
response = handle_logged_in_turn("I love this chatbot!", [], user)
print(response["meta"]["sentiment"])
# Output: {'label': 'positive', 'score': 0.575, 'backend': 'local'}
```

## 4️⃣ Optional: Configure API Keys

For enhanced sentiment analysis, add to `.env`:

```bash
# Hugging Face (Recommended)
HF_API_KEY=your_key_here

# OR Azure Text Analytics
AZURE_LANGUAGE_ENDPOINT=https://your-endpoint.cognitiveservices.azure.com/
AZURE_LANGUAGE_KEY=your_key_here
```

Without API keys, the system uses a local heuristic (works great!).

## 5️⃣ Integration with Production UI

The logged-in bot is already integrated in `production_ui.py`:

```python
# Line 40-42
from logged_in_bot.tools import handle_logged_in_turn

# Line 120-130 (send_message function)
response = handle_logged_in_turn(message, app_state.chat_history, app_state.current_user)
```

Run the production UI:
```bash
python production_ui.py
```

## 📊 Response Structure

Every response includes:

```python
{
    "reply": str,           # Bot's response text
    "meta": {
        "intent": str,      # Detected intent (help, echo, chat, etc.)
        "redacted": bool,   # Whether PII was removed
        "input_len": int,   # Length of processed input
        "sentiment": {
            "label": str,   # positive, neutral, or negative
            "score": float, # Confidence 0.0 to 1.0
            "backend": str  # azure, hf, or local
        }
    }
}
```

## 🧪 Run Tests

```bash
# Validation script
python tools/validate_logged_in_bot.py

# Unit tests (requires pytest)
pytest tests/test_logged_in_bot.py -v
```

## 📚 Learn More

- **Quick Reference**: `logged_in_bot/README.md`
- **Full Documentation**: `docs/LOGGED_IN_BOT_IMPLEMENTATION.md`
- **Completion Report**: `LOGGED_IN_BOT_COMPLETION_REPORT.md`

## 🎯 Supported Commands

| Command | Example |
|---------|---------|
| Help | `help` |
| Echo | `echo Hello World` |
| Summarize | `summarize Long text here...` |
| Remember | `remember name: Anish` |
| Forget | `forget name` |
| List Memory | `list memory` |
| Chat | `What is RAG?` |

## 🔧 Troubleshooting

### Import Error
```bash
# Make sure you're in the project root
cd /home/anish/PycharmProjects/Agentic-Chat-bot-
python -c "from logged_in_bot import handle_logged_in_turn; print('✓ OK')"
```

### No Sentiment
- System uses local heuristic by default (works offline!)
- Add `HF_API_KEY` or Azure credentials for enhanced analysis

### Memory Not Saving
- Check `memory/.profiles/` directory exists
- Verify write permissions
- Memory is saved automatically on each command

## 💡 Pro Tips

1. **No API keys needed** - System works great with local fallbacks
2. **Session management** - Use `memory.sessions.SessionStore` for persistence
3. **PII redaction** - Automatically redacts emails, phones, SSNs, etc.
4. **Extensible** - Easy to add new intents and handlers

## ✅ You're Ready!

The logged-in bot is fully functional and ready to use. Try it in:
- `production_ui.py` (Gradio interface)
- Your own Python scripts
- FastAPI endpoints
- Bot Framework integrations

**Happy coding! 🎉**

---

**Questions?** Check the documentation or run the validation script.
