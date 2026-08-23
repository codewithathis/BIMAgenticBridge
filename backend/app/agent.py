from __future__ import annotations

from typing import Any, Optional

from app.config import Settings
from app.exceptions import ExtractionRequired
from app.gemini_client import build_gemini_client
from app.models import ChatResponse
from app.services.data_readiness import DataReadinessPolicy
from app.services.tool_executor import ToolExecutor
from app.services.tool_loop import ToolLoop


class ChatAgent:
    """Orchestrates readiness policy, tool execution, and the Gemini tool loop."""

    def __init__(
        self,
        settings: Settings,
        client: Optional[Any] = None,
        readiness: Optional[DataReadinessPolicy] = None,
        tool_executor: Optional[ToolExecutor] = None,
        tool_loop: Optional[ToolLoop] = None,
    ) -> None:
        self.settings = settings
        self._client = client
        data_path = settings.resolved_data_json_path
        self._readiness = readiness or DataReadinessPolicy(
            data_path,
            settings.data_ttl_seconds,
        )
        self._tool_executor = tool_executor or ToolExecutor(data_path, self._readiness)
        self._tool_loop = tool_loop

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = build_gemini_client(self.settings)
        return self._client

    def _get_tool_loop(self) -> ToolLoop:
        if self._tool_loop is None:
            self._tool_loop = ToolLoop(self.client, self.settings.gemini_model)
        return self._tool_loop

    def handle_chat(
        self,
        message: str,
        data_ready: bool = False,
        force_extract: bool = False,
    ) -> ChatResponse:
        force_reason = self._readiness.force_extract_required(
            data_ready=data_ready,
            force_extract=force_extract,
        )
        if force_reason:
            return ChatResponse(status="extraction_required", reason=force_reason)

        try:
            reply = self._get_tool_loop().run(
                message,
                on_tool=lambda name, args: self._tool_executor.execute(
                    name,
                    args,
                    data_ready=data_ready,
                ),
            )
            return ChatResponse(status="ok", reply=reply)
        except ExtractionRequired as exc:
            return ChatResponse(status="extraction_required", reason=exc.reason)
