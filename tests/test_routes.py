# /test/test_routes.py
def test_routes_mount():
    from backend.app.main import create_app
    app = create_app()
    paths = [getattr(r, "path", "") for r in app.routes]
    assert "/chatbot/message" in paths
    assert "/health" in paths
