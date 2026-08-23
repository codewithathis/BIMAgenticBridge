"""Select the LLM provider (Gemini or OpenAI) from environment configuration."""

from __future__ import annotations

from typing import Any

from app.config import Settings
from app.exceptions import AgentConfigurationError
from app.gemini_client import build_gemini_client
from app.openai_client import build_openai_client
from app.services.openai_loop import OpenAIToolLoop
from app.services.tool_loop import ToolLoop

_PROVIDER_ALIASES = {
    "gemini": "gemini",
    "google": "gemini",
    "google-genai": "gemini",
    "vertex": "gemini",
    "vertexai": "gemini",
    "adk": "gemini",
    "openai": "openai",
    "gpt": "openai",
}


def resolve_llm_provider(settings: Settings) -> str:
    raw = (settings.llm_provider or "gemini").strip().lower()
    provider = _PROVIDER_ALIASES.get(raw)
    if provider is None:
        raise AgentConfigurationError(
            f"Unsupported LLM_PROVIDER={settings.llm_provider!r}. Use 'gemini' or 'openai'."
        )
    return provider


def resolved_llm_model(settings: Settings) -> str:
    if resolve_llm_provider(settings) == "openai":
        return settings.openai_model
    return settings.gemini_model


def build_llm_client(settings: Settings) -> Any:
    if resolve_llm_provider(settings) == "openai":
        return build_openai_client(settings)
    return build_gemini_client(settings)


def build_tool_loop(settings: Settings, client: Any) -> ToolLoop | OpenAIToolLoop:
    model = resolved_llm_model(settings)
    if resolve_llm_provider(settings) == "openai":
        return OpenAIToolLoop(client, model)
    return ToolLoop(client, model)
