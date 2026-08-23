"""Gemini client factory: API key (AI Studio) or GCP Application Default Credentials."""

from __future__ import annotations

import os
from typing import Any

from google import genai
from google.auth import default as google_auth_default
from google.auth.exceptions import DefaultCredentialsError

from app.config import Settings
from app.exceptions import AgentConfigurationError

_CLOUD_PLATFORM_SCOPE = ("https://www.googleapis.com/auth/cloud-platform",)


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def should_use_vertex_adc(settings: Settings) -> bool:
    """Use Vertex AI + ADC on Cloud Run, with an explicit project, or when requested."""
    if settings.google_genai_use_vertexai:
        return True
    if (settings.google_cloud_project or "").strip():
        return True
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip():
        return True
    # Cloud Run / Cloud Functions inject K_SERVICE.
    if os.environ.get("K_SERVICE", "").strip():
        return True
    if _env_flag("GOOGLE_GENAI_USE_VERTEXAI") or _env_flag("GOOGLE_GENAI_USE_ENTERPRISE"):
        return True
    return False


def build_gemini_client(settings: Settings) -> Any:
    """Create a google-genai Client from GEMINI_API_KEY or GCP ADC."""
    api_key = (settings.gemini_api_key or os.environ.get("GOOGLE_API_KEY") or "").strip()
    if api_key:
        return genai.Client(api_key=api_key)

    if not should_use_vertex_adc(settings):
        raise AgentConfigurationError(
            "GEMINI_API_KEY is not configured and GCP Application Default "
            "Credentials are not enabled. Copy backend/.env.example to "
            "backend/.env and set GEMINI_API_KEY, or set GOOGLE_CLOUD_PROJECT "
            "/ GOOGLE_GENAI_USE_VERTEXAI=true for Vertex AI with ADC."
        )

    project = (settings.google_cloud_project or "").strip() or None
    location = (settings.google_cloud_location or "").strip() or "us-central1"
    try:
        _credentials, adc_project = google_auth_default(scopes=_CLOUD_PLATFORM_SCOPE)
    except DefaultCredentialsError as exc:
        raise AgentConfigurationError(
            "GCP Application Default Credentials were not found. Set "
            "GEMINI_API_KEY, run `gcloud auth application-default login`, or "
            "deploy on Cloud Run with a service account that can call Vertex AI."
        ) from exc

    project = project or adc_project
    return _vertex_or_enterprise_client(project=project, location=location)


def _vertex_or_enterprise_client(*, project: str | None, location: str) -> Any:
    kwargs: dict[str, Any] = {"project": project, "location": location}
    try:
        return genai.Client(vertexai=True, **kwargs)
    except TypeError:
        return genai.Client(enterprise=True, **kwargs)
