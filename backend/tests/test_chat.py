from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.agent import ChatAgent
from app.config import Settings
from app.exceptions import AgentConfigurationError, UpstreamLlmError
from app.main import app
from app.models import ChatResponse
from app.routers import chat as chat_router


class FakeModels:
    def __init__(self, scripted: list[Any]) -> None:
        self._scripted = list(scripted)
        self.calls = 0

    def generate_content(self, **kwargs: Any) -> Any:
        self.calls += 1
        if not self._scripted:
            raise AssertionError("No scripted Gemini responses left")
        return self._scripted.pop(0)


class FakeGeminiClient:
    def __init__(self, scripted: list[Any]) -> None:
        self.models = FakeModels(scripted)

    @property
    def calls(self) -> int:
        return self.models.calls


def _assistant_text(content: str) -> Any:
    return SimpleNamespace(
        function_calls=None,
        text=content,
        candidates=[SimpleNamespace(content=SimpleNamespace(role="model", parts=[]))],
    )


def _assistant_tool_call(arguments: dict[str, Any] | None = None) -> Any:
    args = arguments if arguments is not None else {}
    function_call = SimpleNamespace(name="query_room_data", args=args)
    return SimpleNamespace(
        function_calls=[function_call],
        text=None,
        candidates=[
            SimpleNamespace(
                content=SimpleNamespace(role="model", parts=[SimpleNamespace(function_call=function_call)])
            )
        ],
    )


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["product"] == "BIM Agentic Bridge"
    assert payload["product_slug"] == "bim-agentic-bridge"
    assert "version" in payload
    assert "gemini_api_key" not in payload
    assert "auth_token" not in payload


def test_about() -> None:
    client = TestClient(app)
    response = client.get("/about")
    payload = response.json()
    assert response.status_code == 200
    assert payload["product"] == "BIM Agentic Bridge"
    assert "author" in payload
    assert "github" in payload
    assert "gemini_api_key" not in payload
    assert "auth_token" not in payload


def test_local_health_does_not_send_permissive_cors() -> None:
    """Installed/local backends lock down CORS; hosted (VERCEL) keeps open CORS."""
    client = TestClient(app)
    response = client.get("/health", headers={"Origin": "https://example.com"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


def test_agent_answers_without_tool() -> None:
    settings = Settings(gemini_api_key="test-key", data_ttl_seconds=300)
    client = FakeGeminiClient([_assistant_text("BIM means Building Information Modeling.")])
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("What is BIM?")
    assert result.status == "ok"
    assert "Building Information Modeling" in (result.reply or "")
    assert client.calls == 1


def test_agent_requests_extraction_when_data_missing(tmp_path: Path) -> None:
    settings = Settings(
        gemini_api_key="test-key",
        data_json_path=str(tmp_path / "missing.json"),
        data_ttl_seconds=300,
    )
    client = FakeGeminiClient([_assistant_tool_call({"room_number": "101"})])
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("How many doors in room 101?", data_ready=False)
    assert result.status == "extraction_required"
    assert result.reason is not None


def test_agent_queries_rooms_when_data_ready(sample_rooms_path: Path) -> None:
    settings = Settings(
        gemini_api_key="test-key",
        data_json_path=str(sample_rooms_path),
        data_ttl_seconds=10_000_000,
    )
    client = FakeGeminiClient(
        [
            _assistant_tool_call({"room_number": "101"}),
            _assistant_text("Room 101 has 2 doors and 1 window."),
        ]
    )
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("How many doors in room 101?", data_ready=True)
    assert result.status == "ok"
    assert "2 doors" in (result.reply or "")
    assert client.calls == 2


def test_agent_missing_api_key_raises_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    settings = Settings(
        gemini_api_key="",
        google_cloud_project="",
        google_genai_use_vertexai=False,
        data_ttl_seconds=300,
    )
    agent = ChatAgent(settings)
    with pytest.raises(AgentConfigurationError):
        agent.handle_chat("Hello")


def test_chat_endpoint_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    app.dependency_overrides[chat_router.get_agent] = lambda: ChatAgent(
        Settings(
            gemini_api_key="",
            google_cloud_project="",
            google_genai_use_vertexai=False,
            data_ttl_seconds=300,
        )
    )
    try:
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 503
        detail = response.json()["detail"]
        assert "GEMINI_API_KEY" in detail
    finally:
        app.dependency_overrides.clear()


def test_chat_endpoint_upstream_llm_error() -> None:
    class FailingAgent:
        def handle_chat(self, **kwargs: Any) -> None:
            raise UpstreamLlmError("provider down")

    app.dependency_overrides[chat_router.get_agent] = lambda: FailingAgent()
    try:
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 502
        assert "language model" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_chat_endpoint_unhandled_error_hides_internals() -> None:
    class ExplodingAgent:
        def handle_chat(self, **kwargs: Any) -> None:
            raise RuntimeError("secret internal detail")

    app.dependency_overrides[chat_router.get_agent] = lambda: ExplodingAgent()
    try:
        client = TestClient(app)
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 500
        detail = response.json()["detail"]
        assert "secret internal detail" not in detail
        assert "unexpected error" in detail.lower()
    finally:
        app.dependency_overrides.clear()


def test_chat_endpoint_extraction_required_contract() -> None:
    class ExtractingAgent:
        def handle_chat(self, **kwargs: Any) -> ChatResponse:
            return ChatResponse(status="extraction_required", reason="BIM data missing")

    app.dependency_overrides[chat_router.get_agent] = lambda: ExtractingAgent()
    try:
        client = TestClient(app)
        response = client.post(
            "/chat",
            json={"message": "How many doors in room 101?", "data_ready": False},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "extraction_required"
        assert payload["reason"] == "BIM data missing"
        assert payload.get("reply") in (None, "")
    finally:
        app.dependency_overrides.clear()
