# /app/app.py
from __future__ import annotations
from aiohttp import web
from pathlib import Path
from core.config import settings
from core.logging import setup_logging, get_logger
import json, os

setup_logging(level=settings.log_level, json_logs=settings.json_logs)
log = get_logger("bootstrap")
log.info("starting", extra={"config": settings.to_dict()})

# --- handlers ---
async def home(_req: web.Request) -> web.Response:
    return web.Response(text="Bot is running. POST Bot Framework activities to /api/messages.", content_type="text/plain")

async def healthz(_req: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})

async def messages_get(_req: web.Request) -> web.Response:
    return web.Response(text="This endpoint only accepts POST (Bot Framework activities).", content_type="text/plain", status=405)

async def messages(req: web.Request) -> web.Response:
    return web.Response(status=503, text="Bot Framework disabled in tests.")

def _handle_text(user_text: str) -> str:
    text = (user_text or "").strip()
    if not text:
        return "Please provide text."
    if text.lower() in {"help", "capabilities"}:
        return "Try: reverse <text> | or just say anything"
    if text.lower().startswith("reverse "):
        return text.split(" ", 1)[1][::-1]
    return f"You said: {text}"

async def plain_chat(req: web.Request) -> web.Response:
    try:
        payload = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    reply = _handle_text(payload.get("text", ""))
    return web.json_response({"reply": reply})

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", home)
    app.router.add_get("/healthz", healthz)
    app.router.add_get("/health", healthz)           # <-- add this alias
    app.router.add_get("/api/messages", messages_get)
    app.router.add_post("/api/messages", messages)
    app.router.add_post("/plain-chat", plain_chat)
    app.router.add_post("/chatbot/message", plain_chat)  # <-- test expects this
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.router.add_static("/static/", path=static_dir, show_index=True)
    return app


app = create_app()
