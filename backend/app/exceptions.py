"""Domain exceptions for the chat agent and API layer."""


class ExtractionRequired(Exception):
    """BIM data must be refreshed by the Revit plugin before answering."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class AgentConfigurationError(Exception):
    """Local configuration is incomplete (e.g. missing API key)."""


class UpstreamLlmError(Exception):
    """The upstream LLM provider failed or timed out."""


class ToolExecutionError(Exception):
    """A registered tool failed during execution."""
