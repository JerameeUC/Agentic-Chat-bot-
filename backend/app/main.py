# /backend/app/app.py
# Compatibility shim so tests can import backend.app.main:create_app
# and still reuse your real AIOHTTP app factory.

from app.app import create_app as _create_app

def create_app():
    return _create_app()
