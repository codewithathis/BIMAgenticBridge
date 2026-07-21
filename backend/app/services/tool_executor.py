from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.data_readiness import DataReadinessPolicy
from app.tools.room_query import query_room_data


class ToolExecutor:
    """Executes named agent tools after enforcing data readiness."""

    def __init__(self, data_path: Path, readiness: DataReadinessPolicy) -> None:
        self._data_path = data_path
        self._readiness = readiness

    def execute(self, name: str, arguments_json: str, *, data_ready: bool) -> str:
        if name != "query_room_data":
            return json.dumps({"error": f"Unknown tool: {name}"})

        self._readiness.ensure_ready(data_ready=data_ready)

        try:
            args: dict[str, Any] = json.loads(arguments_json or "{}")
        except json.JSONDecodeError:
            args = {}

        result = query_room_data(
            self._data_path,
            room_number=args.get("room_number"),
            level=args.get("level"),
        )
        return json.dumps(result)
