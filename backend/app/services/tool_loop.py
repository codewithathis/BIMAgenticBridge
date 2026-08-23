from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from google.genai import types

from app.exceptions import UpstreamLlmError
from app.tools.room_query import QUERY_ROOM_DATA_DECLARATION

SYSTEM_PROMPT = """You are BimAgenticBridge, an assistant for BIM room assessment.
Answer clearly in natural language.
When the user asks about rooms, areas, levels, floors, doors, or windows, call query_room_data.
Do not invent room or level inventory.
If rooms are empty, use levels/notes/sourceDocuments from the tool result.
Explain that rooms are usually in Architectural models when the active file is Structural and rooms is empty.
For general BIM questions that do not need model data, answer without tools.
"""

ToolHandler = Callable[[str, str], str]

QUERY_ROOM_DATA_TOOL = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name=QUERY_ROOM_DATA_DECLARATION["name"],
            description=QUERY_ROOM_DATA_DECLARATION["description"],
            parameters_json_schema=QUERY_ROOM_DATA_DECLARATION["parameters"],
        )
    ]
)

GENERATE_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[QUERY_ROOM_DATA_TOOL],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def _function_call_name_and_args(fc: Any) -> tuple[str, dict[str, Any]]:
    inner = getattr(fc, "function_call", None)
    if inner is not None:
        return str(inner.name), dict(inner.args or {})
    return str(fc.name), dict(fc.args or {})


class ToolLoop:
    """Gemini generateContent tool loop (intent / tool resolution only)."""

    def __init__(self, client: Any, model: str, max_rounds: int = 4) -> None:
        self._client = client
        self._model = model
        self._max_rounds = max_rounds

    def run(self, message: str, on_tool: ToolHandler) -> str:
        contents: list[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=message)]),
        ]

        for _ in range(self._max_rounds):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=contents,
                    config=GENERATE_CONFIG,
                )
            except Exception as exc:  # noqa: BLE001 - normalize provider failures
                raise UpstreamLlmError(str(exc)) from exc

            function_calls = list(getattr(response, "function_calls", None) or [])
            candidates = list(getattr(response, "candidates", None) or [])
            if candidates and candidates[0].content is not None:
                contents.append(candidates[0].content)

            if not function_calls:
                text = (getattr(response, "text", None) or "").strip()
                return text or "I do not have an answer."

            function_response_parts: list[types.Part] = []
            for function_call in function_calls:
                name, args = _function_call_name_and_args(function_call)
                tool_result = on_tool(name, json.dumps(args))
                try:
                    payload: dict[str, Any] = json.loads(tool_result)
                    if not isinstance(payload, dict):
                        payload = {"result": payload}
                except json.JSONDecodeError:
                    payload = {"result": tool_result}
                function_response_parts.append(
                    types.Part.from_function_response(name=name, response=payload)
                )

            contents.append(types.Content(role="tool", parts=function_response_parts))

        return "I could not complete the request within the tool-call limit."
