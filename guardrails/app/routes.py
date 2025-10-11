# /app/routes.py — HTTP handlers
# routes.py — HTTP handlers (root-level, no /app package)
import json
from aiohttp import web
# from botbuilder.schema import Activity

# Prefer project logic if available
try:
    from logic import handle_text as _handle_text  # user-defined
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

def init_routes(app: web.Application, adapter, bot) -> None:
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

    # Wire routes
    app.router.add_get("/", home)
    app.router.add_get("/healthz", healthz)
    app.router.add_get("/api/messages", messages_get)
    app.router.add_post("/api/messages", messages)
    app.router.add_post("/plain-chat", plain_chat)
