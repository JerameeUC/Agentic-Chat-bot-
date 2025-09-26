# agenticcore/web_agentic.py
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from agenticcore.chatbot.services import ChatBot

app = FastAPI(title="AgenticCore Web UI")

# 1. Simple HTML form at /
@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <form action="/agentic" method="get">
        <input type="text" name="msg" placeholder="Type a message" style="width:300px">
        <input type="submit" value="Send">
    </form>
    """

# 2. Agentic endpoint
@app.get("/agentic")
def run_agentic(msg: str = Query(..., description="Message to send to ChatBot")):
    bot = ChatBot()
    return bot.reply(msg)
