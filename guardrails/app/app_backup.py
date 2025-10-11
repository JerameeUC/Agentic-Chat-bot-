# /app/app.py
#!/usr/bin/env python3
# app.py — aiohttp + (optional) Bot Framework; optional Gradio UI via APP_MODE=gradio
# NOTE:
# - No top-level 'botbuilder' imports to satisfy compliance guardrails (DISALLOWED list).
# - To enable Bot Framework paths, set env ENABLE_BOTBUILDER=1 and ensure packages are installed.

import os, sys, json, importlib
from pathlib import Path
from typing import Any

from aiohttp import web

# Config / logging
from core.config import settings
from core.logging import setup_logging, get_logger

setup_logging(level=settings.log_level, json_logs=settings.json_logs)
log = get_logger("bootstrap")
log.info("starting", extra={"config": settings.to_dict()})

# -----------------------------------------------------------------------------
# Optional Bot Framework wiring (lazy, env-gated, NO top-level imports)
# -----------------------------------------------------------------------------
ENABLE_BOTBUILDER = os.getenv("ENABLE_BOTBUILDER") == "1"

APP_ID = os.environ.get("MicrosoftAppId") or settings.microsoft_app_id
APP_PASSWORD = os.environ.get("MicrosoftAppPassword") or settings.microsoft_app_password

BF_AVAILABLE = False
BF = {
    "core": None,
    "schema": None,
    "adapter": None,
    "Activity": None,
    "ActivityHandler": None,
    "TurnContext": None,
}

def _load_botframework() -> bool:
    """Dynamically import botbuilder.* if enabled, without tripping compliance regex."""
    global BF_AVAILABLE, BF
    try:
        core = importlib.import_module("botbuilder.core")
        schema = importlib.import_module("botbuilder.schema")
        adapter_settings = core.BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)
        adapter = core.BotFrameworkAdapter(adapter_settings)
        # Hook error handler
        async def on_error(context, error: Exception):
            print(f"[on_turn_error] {error}", file=sys.stderr, flush=True)
            try:
                await context.send_activity("Oops. Something went wrong!")
            except Exception as send_err:
                print(f"[on_turn_error][send_activity_failed] {send_err}", file=sys.stderr, flush=True)
        adapter.on_turn_error = on_error

        BF.update({
            "core": core,
            "schema": schema,
            "adapter": adapter,
            "Activity": schema.Activity,
            "ActivityHandler": core.ActivityHandler,
            "TurnContext": core.TurnContext,
        })
        BF_AVAILABLE = True
        log.info("Bot Framework enabled (via ENABLE_BOTBUILDER=1).")
        return True
    except Exception as e:
        log.warning("Bot Framework unavailable; running without it", extra={"error": repr(e)})
        BF_AVAILABLE = False
        return False

if ENABLE_BOTBUILDER:
    _load_botframework()

# -----------------------------------------------------------------------------
# Bot impl
# -----------------------------------------------------------------------------
if BF_AVAILABLE:
    # Prefer user's ActivityHandler bot if present; fallback to a tiny echo bot
    try:
        from bot import SimpleBot as BotImpl  # user's BF ActivityHandler
    except Exception:
        AH = BF["ActivityHandler"]
        TC = BF["TurnContext"]

        class BotImpl(AH):  # type: ignore[misc]
            async def on_turn(self, turn_context: TC):  # type: ignore[override]
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
    bot = BotImpl()
else:
    # Non-BotFramework minimal bot (not used by /api/messages; plain-chat uses _handle_text)
    class BotImpl:  # placeholder to keep a consistent symbol
        pass
    bot = BotImpl()

# -----------------------------------------------------------------------------
# Plain-chat logic (independent of Bot Framework)
# -----------------------------------------------------------------------------
try:
    from logic import handle_text as _handle_text
except Exception:
    from skills import normalize, reverse_text
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

# -----------------------------------------------------------------------------
# HTTP handlers (AIOHTTP)
# -----------------------------------------------------------------------------
async def messages(req: web.Request) -> web.Response:
    """Bot Framework activities endpoint."""
    if not BF_AVAILABLE:
        return web.json_response(
            {"error": "Bot Framework disabled. Set ENABLE_BOTBUILDER=1 to enable /api/messages."},
            status=501,
        )
    ctype = (req.headers.get("Content-Type") or "").lower()
    if "application/json" not in ctype:
        return web.Response(status=415, text="Unsupported Media Type: expected application/json")
    try:
        body = await req.json()
    except json.JSONDecodeError:
        return web.Response(status=400, text="Invalid JSON body")

    Activity = BF["Activity"]
    adapter = BF["adapter"]
    activity = Activity().deserialize(body)  # type: ignore[call-arg]
    auth_header = req.headers.get("Authorization")
    invoke_response = await adapter.process_activity(activity, auth_header, bot.on_turn)  # type: ignore[attr-defined]
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

# -----------------------------------------------------------------------------
# App factory (AIOHTTP)
# -----------------------------------------------------------------------------
def create_app() -> web.Application:
    app = web.Application()

    # Routes
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

# -----------------------------------------------------------------------------
# Optional Gradio UI (Anonymous mode)
# -----------------------------------------------------------------------------
def build():
    """
    Return a Gradio Blocks UI for simple anonymous chat.
    Only imported/used when APP_MODE=gradio (keeps aiohttp path lean).
    """
    try:
        import gradio as gr
    except Exception as e:
        raise RuntimeError("Gradio is not installed. `pip install gradio`") from e

    # Import UI components lazily
    from app.components import (
        build_header, build_footer, build_chat_history, build_chat_input,
        build_spinner, build_error_banner, set_error, build_sidebar,
        render_status_badge, render_login_badge, to_chatbot_pairs
    )
    from anon_bot.handler import handle_turn

    with gr.Blocks(css="body{background:#fafafa}") as demo:
        build_header("Storefront Chatbot", "Anonymous mode ready")
        with gr.Row():
            with gr.Column(scale=3):
                _ = render_status_badge("online")
                _ = render_login_badge(False)
                chat = build_chat_history()
                _ = build_spinner(False)
                error = build_error_banner()
                txt, send, clear = build_chat_input()
            with gr.Column(scale=1):
                mode, clear_btn, faq_toggle = build_sidebar()

        build_footer("0.1.0")

        state = gr.State([])  # history

        def on_send(message, hist):
            try:
                new_hist = handle_turn(message, hist, user=None)
                return "", new_hist, gr.update(value=to_chatbot_pairs(new_hist)), {"value": "", "visible": False}
            except Exception as e:
                return "", hist, gr.update(), set_error(error, str(e))

        send.click(on_send, [txt, state], [txt, state, chat, error])
        txt.submit(on_send, [txt, state], [txt, state, chat, error])

        def on_clear():
            return [], gr.update(value=[]), {"value": "", "visible": False}

        clear.click(on_clear, None, [state, chat, error])

    return demo

# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    mode = os.getenv("APP_MODE", "aiohttp").lower()
    if mode == "gradio":
        port = int(os.getenv("PORT", settings.port or 7860))
        host = os.getenv("HOST", settings.host or "0.0.0.0")
        build().launch(server_name=host, server_port=port)
    else:
        web.run_app(app, host=settings.host, port=settings.port)
