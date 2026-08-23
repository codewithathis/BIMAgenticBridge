"""OpenAI client factory."""

from __future__ import annotations

from typing import Any

from openai import OpenAI

from app.config import Settings
from app.exceptions import AgentConfigurationError


def build_openai_client(settings: Settings) -> Any:
    api_key = (settings.openai_api_key or "").strip()
    if not api_key:
        raise AgentConfigurationError(
            "OPENAI_API_KEY is not configured. Set LLM_PROVIDER=gemini to use Gemini, "
            "or copy backend/.env.example to backend/.env and set OPENAI_API_KEY."
        )
    return OpenAI(api_key=api_key)
