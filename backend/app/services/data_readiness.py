from __future__ import annotations

from pathlib import Path

from app.exceptions import ExtractionRequired
from app.tools.room_query import check_data_availability


class DataReadinessPolicy:
    """Decides whether local BIM export data is usable for tool calls."""

    def __init__(self, data_path: Path, ttl_seconds: int) -> None:
        self._data_path = data_path
        self._ttl_seconds = ttl_seconds

    def ensure_ready(self, *, data_ready: bool) -> None:
        availability = check_data_availability(self._data_path, self._ttl_seconds)

        if not availability.exists:
            if data_ready:
                raise ExtractionRequired(
                    f"data.json still missing after extraction at {self._data_path}"
                )
            raise ExtractionRequired(
                f"BIM data missing at {self._data_path}. Trigger Revit extraction."
            )

        if availability.error:
            raise ExtractionRequired(availability.error)

        if availability.stale and not data_ready:
            raise ExtractionRequired(
                "BIM data is stale. Trigger Revit extraction for real-time values."
            )

    def force_extract_required(self, *, data_ready: bool, force_extract: bool) -> str | None:
        if force_extract and not data_ready:
            return "Client requested a fresh Revit extraction."
        return None
