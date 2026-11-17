from fastapi.testclient import TestClient

from app.config import Settings, clear_settings_cache
from app.main import app


def test_chat_requires_token_when_auth_enabled(monkeypatch) -> None:
    monkeypatch.setenv("REQUIRE_AUTH", "true")
    monkeypatch.setenv("AUTH_TOKEN", "secret-token")
    clear_settings_cache()
    try:
        client = TestClient(app)
        denied = client.post("/chat", json={"message": "hi"})
        assert denied.status_code == 401

        ok_health = client.get("/health")
        assert ok_health.status_code == 200

        # Still 503/502/etc after auth — but not 401.
        allowed = client.post(
            "/chat",
            json={"message": "hi"},
            headers={"X-BimAgentic-Token": "secret-token"},
        )
        assert allowed.status_code != 401
    finally:
        monkeypatch.delenv("REQUIRE_AUTH", raising=False)
        monkeypatch.delenv("AUTH_TOKEN", raising=False)
        clear_settings_cache()
