#!/usr/bin/env python3
# app/app.py — aiohttp + Bot Framework bootstrap

import os, sys
from aiohttp import web
from pathlib import Path
from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings, TurnContext

from app.routes import init_routes
from bot import SimpleBot

# Credentials
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

# Bot instance
bot = SimpleBot()

def create_app() -> web.Application:
    app = web.Application()
    init_routes(app, adapter, bot)

    # Optional CORS
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

    # Static folder if present
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
