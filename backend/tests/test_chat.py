from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.agent import ChatAgent
from app.config import Settings
from app.main import app


class FakeCompletions:
    def __init__(self, scripted: list[Any]) -> None:
        self._scripted = list(scripted)
        self.calls = 0

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        if not self._scripted:
            raise AssertionError("No scripted OpenAI responses left")
        return self._scripted.pop(0)


def _assistant_text(content: str) -> Any:
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def _assistant_tool_call(tool_call_id: str = "call_1", arguments: str = "{}") -> Any:
    tool_call = SimpleNamespace(
        id=tool_call_id,
        function=SimpleNamespace(name="query_room_data", arguments=arguments),
    )
    message = SimpleNamespace(content=None, tool_calls=[tool_call])
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agent_answers_without_tool() -> None:
    settings = Settings(openai_api_key="test-key", data_ttl_seconds=300)
    fake = FakeCompletions([_assistant_text("BIM means Building Information Modeling.")])
    client = MagicMock()
    client.chat.completions = fake
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("What is BIM?")
    assert result.status == "ok"
    assert "Building Information Modeling" in (result.reply or "")
    assert fake.calls == 1


def test_agent_requests_extraction_when_data_missing(tmp_path: Path) -> None:
    settings = Settings(
        openai_api_key="test-key",
        data_json_path=str(tmp_path / "missing.json"),
        data_ttl_seconds=300,
    )
    fake = FakeCompletions([_assistant_tool_call(arguments='{"room_number":"101"}')])
    client = MagicMock()
    client.chat.completions = fake
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("How many doors in room 101?", data_ready=False)
    assert result.status == "extraction_required"
    assert result.reason is not None


def test_agent_queries_rooms_when_data_ready(sample_rooms_path: Path) -> None:
    settings = Settings(
        openai_api_key="test-key",
        data_json_path=str(sample_rooms_path),
        data_ttl_seconds=10_000_000,
    )
    fake = FakeCompletions(
        [
            _assistant_tool_call(arguments='{"room_number":"101"}'),
            _assistant_text("Room 101 has 2 doors and 1 window."),
        ]
    )
    client = MagicMock()
    client.chat.completions = fake
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("How many doors in room 101?", data_ready=True)
    assert result.status == "ok"
    assert "2 doors" in (result.reply or "")
    assert fake.calls == 2


def test_chat_endpoint_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    client = TestClient(app)
    # Force settings reload without key
    monkeypatch.setattr(
        "app.routers.chat.get_settings",
        lambda: Settings(openai_api_key="", data_ttl_seconds=300),
    )
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 503
