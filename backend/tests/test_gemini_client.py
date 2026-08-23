import os
from unittest.mock import patch

import pytest

from app.config import Settings
from app.exceptions import AgentConfigurationError
from app.gemini_client import build_gemini_client, should_use_vertex_adc


def test_should_use_vertex_when_flag_set() -> None:
    settings = Settings(gemini_api_key="", google_genai_use_vertexai=True)
    assert should_use_vertex_adc(settings) is True


def test_should_use_vertex_when_project_set() -> None:
    settings = Settings(gemini_api_key="", google_cloud_project="demo-project")
    assert should_use_vertex_adc(settings) is True


def test_should_use_vertex_on_cloud_run() -> None:
    settings = Settings(gemini_api_key="")
    with patch.dict(os.environ, {"K_SERVICE": "bim-agentic-bridge"}, clear=False):
        assert should_use_vertex_adc(settings) is True


def test_local_dev_without_key_does_not_imply_adc() -> None:
    settings = Settings(
        gemini_api_key="",
        google_cloud_project="",
        google_genai_use_vertexai=False,
    )
    env = {
        key: value
        for key, value in os.environ.items()
        if key
        not in {
            "K_SERVICE",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GOOGLE_GENAI_USE_VERTEXAI",
            "GOOGLE_GENAI_USE_ENTERPRISE",
            "GOOGLE_CLOUD_PROJECT",
        }
    }
    with patch.dict(os.environ, env, clear=True):
        assert should_use_vertex_adc(settings) is False
        with pytest.raises(AgentConfigurationError, match="GEMINI_API_KEY"):
            build_gemini_client(settings)
