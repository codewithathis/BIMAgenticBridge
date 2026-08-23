from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.agent import ChatAgent
from app.config import Settings
from app.exceptions import AgentConfigurationError
from app.llm import build_tool_loop, resolve_llm_provider


def test_resolve_provider_aliases() -> None:
    assert resolve_llm_provider(Settings(llm_provider="Gemini")) == "gemini"
    assert resolve_llm_provider(Settings(llm_provider="google")) == "gemini"
    assert resolve_llm_provider(Settings(llm_provider="gpt")) == "openai"
    assert resolve_llm_provider(Settings(llm_provider="openai")) == "openai"


def test_resolve_provider_rejects_unknown() -> None:
    with pytest.raises(AgentConfigurationError, match="Unsupported LLM_PROVIDER"):
        resolve_llm_provider(Settings(llm_provider="claude"))


def test_openai_missing_key_raises_configuration_error() -> None:
    settings = Settings(llm_provider="openai", openai_api_key="", data_ttl_seconds=300)
    agent = ChatAgent(settings)
    with pytest.raises(AgentConfigurationError, match="OPENAI_API_KEY"):
        agent.handle_chat("Hello")


def test_openai_agent_answers_without_tool() -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        openai_model="gpt-4o-mini",
        data_ttl_seconds=300,
    )
    message = SimpleNamespace(content="BIM means Building Information Modeling.", tool_calls=None)
    response = SimpleNamespace(choices=[SimpleNamespace(message=message)])
    completions = MagicMock()
    completions.create.return_value = response
    client = MagicMock()
    client.chat.completions = completions
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("What is BIM?")
    assert result.status == "ok"
    assert "Building Information Modeling" in (result.reply or "")
    completions.create.assert_called_once()


def test_openai_agent_queries_rooms_when_data_ready(sample_rooms_path: Any) -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        data_json_path=str(sample_rooms_path),
        data_ttl_seconds=10_000_000,
    )
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(name="query_room_data", arguments='{"room_number":"101"}'),
    )
    first = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=None, tool_calls=[tool_call]))]
    )
    second = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="Room 101 has 2 doors and 1 window.", tool_calls=None)
            )
        ]
    )
    completions = MagicMock()
    completions.create.side_effect = [first, second]
    client = MagicMock()
    client.chat.completions = completions
    agent = ChatAgent(settings, client=client)

    result = agent.handle_chat("How many doors in room 101?", data_ready=True)
    assert result.status == "ok"
    assert "2 doors" in (result.reply or "")
    assert completions.create.call_count == 2


def test_build_tool_loop_selects_openai() -> None:
    settings = Settings(llm_provider="openai", openai_api_key="test-key")
    loop = build_tool_loop(settings, client=MagicMock())
    assert loop.__class__.__name__ == "OpenAIToolLoop"


def test_build_tool_loop_selects_gemini() -> None:
    settings = Settings(llm_provider="gemini", gemini_api_key="test-key")
    loop = build_tool_loop(settings, client=MagicMock())
    assert loop.__class__.__name__ == "ToolLoop"
