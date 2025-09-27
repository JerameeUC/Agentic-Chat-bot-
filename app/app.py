# /app/app.py
#!/usr/bin/env python3
# app.py — aiohttp + Bot Framework (root-level). Routes added explicitly.
import os, sys, json
from aiohttp import web
from pathlib import Path
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext, ActivityHandler
from botbuilder.schema import Activity

# Config / logging
from core.config import settings
from core.logging import setup_logging, get_logger

setup_logging(level=settings.log_level, json_logs=settings.json_logs)
log = get_logger("bootstrap")
log.info("starting", extra={"config": settings.to_dict()})

# Bot impl: prefer user's SimpleBot, fallback to tiny bot
try:
    from bot import SimpleBot as BotImpl  # user's ActivityHandler
except Exception:
    class BotImpl(ActivityHandler):
        async def on_turn(self, turn_context: TurnContext):
            if (turn_context.activity.type or "").lower() == "message":
                text = (turn_context.activity.text or "").strip()
                if not text:
                    await turn_context.send_activity("Input was empty. Type 'help' for usage.")
                    return
                lower = text.lower()
                if lower == "help":
                    await turn_context.send_activity("Try: echo <msg> | reverse: <msg> | capabilities")
                elif lower == "capabilities":
                    await turn_context.send_activity("- echo\n- reverse\n- help\n- capabilities")
                elif lower.startswith("reverse:"):
                    payload = text.split(":", 1)[1].strip()
                    await turn_context.send_activity(payload[::-1])
                elif lower.startswith("echo "):
                    await turn_context.send_activity(text[5:])
                else:
                    await turn_context.send_activity("Unsupported command. Type 'help' for examples.")
            else:
                await turn_context.send_activity(f"[{turn_context.activity.type}] event received.")

# Adapter / credentials
APP_ID = os.environ.get("MicrosoftAppId") or settings.microsoft_app_id
APP_PASSWORD = os.environ.get("MicrosoftAppPassword") or settings.microsoft_app_password
adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

async def on_error(context: TurnContext, error: Exception):
    print(f"[on_turn_error] {error}", file=sys.stderr, flush=True)
    try:
        await context.send_activity("Oops. Something went wrong!")
    except Exception as send_err:
        print(f"[on_turn_error][send_activity_failed] {send_err}", file=sys.stderr, flush=True)

adapter.on_turn_error = on_error
bot = BotImpl()

# Prefer project logic for /plain-chat; otherwise fallback to simple helpers
try:
    from logic import handle_text as _handle_text
except Exception:
    from skills import normalize, reverse_text, is_empty
    def _handle_text(user_text: str) -> str:
        text = (user_text or "").strip()
        if not text:
            return "Please provide text."
        cmd = normalize(text)
        if cmd in {"help", "capabilities"}:
            return "Try: reverse <text> | or just say anything"
        if cmd.startswith("reverse "):
            original = text.split(" ", 1)[1] if " " in text else ""
            return reverse_text(original)
        return f"You said: {text}"

# -------------------- HTTP handlers (module-level) --------------------
async def messages(req: web.Request) -> web.Response:
    ctype = (req.headers.get("Content-Type") or "").lower()
    if "application/json" not in ctype:
        return web.Response(status=415, text="Unsupported Media Type: expected application/json")
    try:
        body = await req.json()
    except json.JSONDecodeError:
        return web.Response(status=400, text="Invalid JSON body")

    activity = Activity().deserialize(body)
    auth_header = req.headers.get("Authorization")
    invoke_response = await adapter.process_activity(activity, auth_header, bot.on_turn)
    if invoke_response:
        return web.json_response(data=invoke_response.body, status=invoke_response.status)
    return web.Response(status=202, text="Accepted")

async def messages_get(_req: web.Request) -> web.Response:
    return web.Response(
        text="This endpoint only accepts POST (Bot Framework activities).",
        content_type="text/plain",
        status=405
    )

async def home(_req: web.Request) -> web.Response:
    return web.Response(
        text="Bot is running. POST Bot Framework activities to /api/messages.",
        content_type="text/plain"
    )

async def healthz(_req: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})

async def plain_chat(req: web.Request) -> web.Response:
    try:
        payload = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    user_text = payload.get("text", "")
    reply = _handle_text(user_text)
    return web.json_response({"reply": reply})

# -------------------- App factory --------------------
def create_app() -> web.Application:
    app = web.Application()

    # Add routes explicitly (as requested)
    app.router.add_get("/", home)
    app.router.add_get("/healthz", healthz)
    app.router.add_get("/api/messages", messages_get)
    app.router.add_post("/api/messages", messages)
    app.router.add_post("/plain-chat", plain_chat)

    # Optional CORS (if installed)
    try:
        import aiohttp_cors
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods=["GET","POST","OPTIONS"],
            )
        })
        for route in list(app.router.routes()):
            cors.add(route)
    except Exception:
        pass

    # Static (./static)
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.router.add_static("/static/", path=static_dir, show_index=True)
    else:
        log.warning("static directory not found", extra={"path": str(static_dir)})

    return app

app = create_app()

if __name__ == "__main__":
    web.run_app(app, host=settings.host, port=settings.port)
