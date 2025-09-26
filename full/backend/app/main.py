# backend/app/main.py
from __future__ import annotations

import os
import time
import traceback
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


def create_app() -> FastAPI:
    app = FastAPI(title="AgenticCore Backend")

    # --- CORS: allow local dev origins + file:// (appears as 'null') ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000", "http://localhost:3000",
            "http://127.0.0.1:5173", "http://localhost:5173",
            "http://127.0.0.1:8080", "http://localhost:8080",
            "http://127.0.0.1:8000", "http://localhost:8000",
            "null",  # file:// pages in some browsers
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"ok": True, "version": "0.3.0", "time": int(time.time())}

    @app.get("/status")
    def status():
        provider = os.getenv("AI_PROVIDER") or "auto"
        return {"provider": provider}

    # --- Routers ---
    try:
        from backend.app.routers.chatbot import router as chatbot_router
        app.include_router(chatbot_router)  # exposes POST /chatbot/message
        print("✅ Chatbot router mounted at /chatbot")
    except Exception as e:
        print("❌ Failed to mount chatbot router:", e)
        traceback.print_exc()

    # --- Static frontends served by FastAPI (same-origin -> no CORS) ---
    FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
    app.mount("/ui2", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

    # Keep your existing single-file UI at /ui (optional)
    FRONTEND_FILE = FRONTEND_DIR / "agenticcore_frontend.html"

    @app.get("/ui", response_class=HTMLResponse)
    def ui():
        try:
            return FRONTEND_FILE.read_text(encoding="utf-8")
        except Exception:
            return HTMLResponse("<h1>UI not found</h1>", status_code=404)

    return app


# Uvicorn entrypoint
app = create_app()
