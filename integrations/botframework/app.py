# /intergrations/botframework/app.py — aiohttp + Bot Framework Echo bot
#!/usr/bin/env python3

import os
import sys
import json
from logic import handle_text
from aiohttp import web
# from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext
# from botbuilder.schema import Activity
import aiohttp_cors
from pathlib import Path


# -------------------------------------------------------------------
# Your bot implementation
# -------------------------------------------------------------------
# Make sure this exists at packages/bots/echo_bot.py
# from bots.echo_bot import EchoBot
# Minimal inline fallback if you want to test quickly:
class EchoBot:
    async def on_turn(self, turn_context: TurnContext):
        if turn_context.activity.type == "message":
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

# -------------------------------------------------------------------
# Adapter / bot setup
# -------------------------------------------------------------------
APP_ID = os.environ.get("MicrosoftAppId") or None
APP_PASSWORD = os.environ.get("MicrosoftAppPassword") or None

adapter_settings = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
adapter = BotFrameworkAdapter(adapter_settings)

async def on_error(context: TurnContext, error: Exception):
    print(f"[on_turn_error] {error}", file=sys.stderr, flush=True)
    try:
        await context.send_activity("Oops. Something went wrong!")
    except Exception as send_err:
        print(f"[on_turn_error][send_activity_failed] {send_err}", file=sys.stderr, flush=True)

adapter.on_turn_error = on_error
bot = EchoBot()

# -------------------------------------------------------------------
# HTTP handlers
# -------------------------------------------------------------------
async def messages(req: web.Request) -> web.Response:
    # Content-Type can include charset; do a contains check
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
        # For invoke activities, adapter returns explicit status/body
        return web.json_response(data=invoke_response.body, status=invoke_response.status)
    # Acknowledge standard message activities
    return web.Response(status=202, text="Accepted")

async def home(_req: web.Request) -> web.Response:
    return web.Response(
        text="Bot is running. POST Bot Framework activities to /api/messages.",
        content_type="text/plain"
    )

async def messages_get(_req: web.Request) -> web.Response:
    return web.Response(
        text="This endpoint only accepts POST (Bot Framework activities).",
        content_type="text/plain",
        status=405
    )

async def healthz(_req: web.Request) -> web.Response:
    return web.json_response({"status": "ok"})

async def plain_chat(req: web.Request) -> web.Response:
    try:
        payload = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    user_text = payload.get("text", "")
    reply = handle_text(user_text)
    return web.json_response({"reply": reply})

# -------------------------------------------------------------------
# App factory and entrypoint
# -------------------------------------------------------------------
from pathlib import Path

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", home)
    app.router.add_get("/healthz", healthz)
    app.router.add_get("/api/messages", messages_get)
    app.router.add_post("/api/messages", messages)
    app.router.add_post("/plain-chat", plain_chat)

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.router.add_static("/static/", path=static_dir, show_index=True)
    else:
        print(f"[warn] static directory not found: {static_dir}", flush=True)

    return app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")  # use 0.0.0.0 in containers
    port = int(os.environ.get("PORT", 3978))
    web.run_app(app, host=host, port=port)
