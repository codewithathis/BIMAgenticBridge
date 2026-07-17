from __future__ import annotations

import json
from typing import Any, Optional

from openai import OpenAI

from app.config import Settings
from app.models import ChatResponse
from app.tools.room_query import (
    QUERY_ROOM_DATA_TOOL,
    check_data_availability,
    query_room_data,
)

SYSTEM_PROMPT = """You are BimAgenticBridge, an assistant for BIM room assessment.
Answer clearly in natural language.
When the user asks about rooms, areas, levels, doors, or windows, call query_room_data.
Do not invent room inventory. If the tool returns no matches, say so.
For general BIM questions that do not need model data, answer without tools.
"""


class ExtractionRequired(Exception):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class ChatAgent:
    def __init__(self, settings: Settings, client: Optional[OpenAI] = None) -> None:
        self.settings = settings
        self._client = client

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.settings.openai_api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not configured. Copy backend/.env.example to "
                    "backend/.env and set your key."
                )
            self._client = OpenAI(api_key=self.settings.openai_api_key)
        return self._client

    def handle_chat(self, message: str, data_ready: bool = False, force_extract: bool = False) -> ChatResponse:
        data_path = self.settings.resolved_data_json_path
        availability = check_data_availability(data_path, self.settings.data_ttl_seconds)

        if force_extract and not data_ready:
            return ChatResponse(
                status="extraction_required",
                reason="Client requested a fresh Revit extraction.",
            )

        if not availability.exists and not data_ready:
            # Let the model run first; if it calls the tool we require extraction.
            pass

        try:
            reply = self._run_tool_loop(message, data_ready=data_ready)
            return ChatResponse(status="ok", reply=reply)
        except ExtractionRequired as exc:
            return ChatResponse(status="extraction_required", reason=exc.reason)

    def _ensure_data_for_tool(self, data_ready: bool) -> None:
        data_path = self.settings.resolved_data_json_path
        availability = check_data_availability(data_path, self.settings.data_ttl_seconds)

        if not availability.exists:
            if data_ready:
                raise ExtractionRequired(
                    f"data.json still missing after extraction at {data_path}"
                )
            raise ExtractionRequired(
                f"BIM data missing at {data_path}. Trigger Revit extraction."
            )

        if availability.error:
            raise ExtractionRequired(availability.error)

        if availability.stale and not data_ready:
            raise ExtractionRequired(
                "BIM data is stale. Trigger Revit extraction for real-time values."
            )

    def _execute_tool(self, name: str, arguments_json: str, data_ready: bool) -> str:
        if name != "query_room_data":
            return json.dumps({"error": f"Unknown tool: {name}"})

        self._ensure_data_for_tool(data_ready=data_ready)

        try:
            args = json.loads(arguments_json or "{}")
        except json.JSONDecodeError:
            args = {}

        result = query_room_data(
            self.settings.resolved_data_json_path,
            room_number=args.get("room_number"),
            level=args.get("level"),
        )
        return json.dumps(result)

    def _run_tool_loop(self, message: str, data_ready: bool, max_rounds: int = 4) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]

        for _ in range(max_rounds):
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                tools=[QUERY_ROOM_DATA_TOOL],
                tool_choice="auto",
            )
            choice = response.choices[0]
            assistant_message = choice.message
            tool_calls = assistant_message.tool_calls or []

            messages.append(
                {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ]
                    if tool_calls
                    else None,
                }
            )

            # Remove null tool_calls for cleaner payload when absent.
            if messages[-1].get("tool_calls") is None:
                messages[-1].pop("tool_calls", None)

            if not tool_calls:
                return (assistant_message.content or "").strip() or "I do not have an answer."

            for tool_call in tool_calls:
                tool_result = self._execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments,
                    data_ready=data_ready,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

        return "I could not complete the request within the tool-call limit."
