# backend/app/main.py
from app.app import create_app as _create_app

class _RouteView:
    def __init__(self, path: str) -> None:
        self.path = path

def create_app():
    app = _create_app()

    # --- test-compat: add app.routes with .path attributes ---
    try:
        paths = set()
        for r in app.router.routes():
            info = r.resource.get_info()
            path = info.get("path") or info.get("formatter")
            if isinstance(path, str):
                paths.add(path)
        # attach for pytest
        app.routes = [_RouteView(p) for p in sorted(paths)]  # type: ignore[attr-defined]
    except Exception:
        app.routes = []  # type: ignore[attr-defined]

    return app
