from __future__ import annotations

from typing import Any

from app.exceptions import UpstreamLlmError
from app.services.tool_loop import SYSTEM_PROMPT, ToolHandler
from app.tools.room_query import QUERY_ROOM_DATA_DECLARATION

OPENAI_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": QUERY_ROOM_DATA_DECLARATION["name"],
            "description": QUERY_ROOM_DATA_DECLARATION["description"],
            "parameters": {
                **QUERY_ROOM_DATA_DECLARATION["parameters"],
                "additionalProperties": False,
            },
        },
    }
]


class OpenAIToolLoop:
    """OpenAI chat-completions tool loop (intent / tool resolution only)."""

    def __init__(self, client: Any, model: str, max_rounds: int = 4) -> None:
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
                    tools=OPENAI_TOOLS,
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
