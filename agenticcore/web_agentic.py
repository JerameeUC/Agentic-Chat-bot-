# /agenticcore/web_agentic.py
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles  # <-- ADD THIS
from agenticcore.chatbot.services import ChatBot
import pathlib
import os

app = FastAPI(title="AgenticCore Web UI")

# 1) Simple HTML form at /
@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <head>
      <link rel="icon" type="image/png" href="/static/favicon.png">
      <title>AgenticCore</title>
    </head>
    <form action="/agentic" method="get" style="padding:16px;">
        <input type="text" name="msg" placeholder="Type a message" style="width:300px">
        <input type="submit" value="Send">
    </form>
    """

# 2) Agentic endpoint
@app.get("/agentic")
def run_agentic(msg: str = Query(..., description="Message to send to ChatBot")):
    bot = ChatBot()
    return bot.reply(msg)

# --- Static + favicon setup ---

# TIP: we're inside <repo>/agenticcore/web_agentic.py
# repo root = parents[1]
repo_root = pathlib.Path(__file__).resolve().parents[1]

# Put static assets under app/assets/html
assets_path = repo_root / "app" / "assets" / "html"
assets_path_str = str(assets_path)

# Mount /static so /static/favicon.png works
app.mount("/static", StaticFiles(directory=assets_path_str), name="static")

# Serve /favicon.ico (browsers request this path)
@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    png = assets_path / "favicon.ico"
    if png.exists():
        return FileResponse(str(ico), media_type="image/ico")
    # Graceful fallback: return an empty 204 if icon missing
    return HTMLResponse(status_code=204, content="")
