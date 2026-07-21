from __future__ import annotations

from collections.abc import Callable
from typing import Any

from openai import OpenAI

from app.exceptions import UpstreamLlmError
from app.tools.room_query import QUERY_ROOM_DATA_TOOL

SYSTEM_PROMPT = """You are BimAgenticBridge, an assistant for BIM room assessment.
Answer clearly in natural language.
When the user asks about rooms, areas, levels, floors, doors, or windows, call query_room_data.
Do not invent room or level inventory.
If rooms are empty, use levels/notes/sourceDocuments from the tool result.
Explain that rooms are usually in Architectural models when the active file is Structural and rooms is empty.
For general BIM questions that do not need model data, answer without tools.
"""

ToolHandler = Callable[[str, str], str]


class ToolLoop:
    """OpenAI chat-completions tool loop (intent / tool resolution only)."""

    def __init__(self, client: OpenAI, model: str, max_rounds: int = 4) -> None:
        self._client = client
        self._model = model
        self._max_rounds = max_rounds

    def run(self, message: str, on_tool: ToolHandler) -> str:
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ]

        for _ in range(self._max_rounds):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    tools=[QUERY_ROOM_DATA_TOOL],
                    tool_choice="auto",
                )
            except Exception as exc:  # noqa: BLE001 - normalize provider failures
                raise UpstreamLlmError(str(exc)) from exc

            choice = response.choices[0]
            assistant_message = choice.message
            tool_calls = assistant_message.tool_calls or []

            assistant_payload: dict[str, Any] = {
                "role": "assistant",
                "content": assistant_message.content,
            }
            if tool_calls:
                assistant_payload["tool_calls"] = [
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
            messages.append(assistant_payload)

            if not tool_calls:
                return (assistant_message.content or "").strip() or "I do not have an answer."

            for tool_call in tool_calls:
                tool_result = on_tool(tool_call.function.name, tool_call.function.arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

        return "I could not complete the request within the tool-call limit."
