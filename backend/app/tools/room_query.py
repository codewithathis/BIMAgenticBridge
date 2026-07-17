from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class DataAvailability:
    exists: bool
    stale: bool
    path: Path
    age_seconds: Optional[float] = None
    error: Optional[str] = None


def check_data_availability(path: Path, ttl_seconds: int) -> DataAvailability:
    if not path.exists():
        return DataAvailability(exists=False, stale=True, path=path, error="data.json not found")

    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return DataAvailability(
            exists=True,
            stale=True,
            path=path,
            error=f"Failed to read data.json: {exc}",
        )

    exported_at = payload.get("exportedAtUtc")
    age_seconds: Optional[float] = None
    stale = False

    if exported_at:
        try:
            exported_dt = datetime.fromisoformat(exported_at.replace("Z", "+00:00"))
            if exported_dt.tzinfo is None:
                exported_dt = exported_dt.replace(tzinfo=timezone.utc)
            age_seconds = (datetime.now(timezone.utc) - exported_dt).total_seconds()
            stale = age_seconds > ttl_seconds
        except ValueError:
            stale = True
            return DataAvailability(
                exists=True,
                stale=True,
                path=path,
                error="Invalid exportedAtUtc timestamp",
            )
    else:
        # Fall back to file mtime when export timestamp is missing.
        age_seconds = datetime.now(timezone.utc).timestamp() - path.stat().st_mtime
        stale = age_seconds > ttl_seconds

    return DataAvailability(exists=True, stale=stale, path=path, age_seconds=age_seconds)


def load_rooms(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("data.json root must be an object")
    rooms = payload.get("rooms", [])
    if not isinstance(rooms, list):
        raise ValueError("rooms must be a list")
    return payload


def query_room_data(
    path: Path,
    room_number: Optional[str] = None,
    level: Optional[str] = None,
) -> dict[str, Any]:
    """Load and optionally filter rooms from the exported JSON file."""
    payload = load_rooms(path)
    rooms = payload.get("rooms", [])

    filtered = rooms
    if room_number:
        needle = room_number.strip().lower()
        filtered = [r for r in filtered if str(r.get("number", "")).strip().lower() == needle]
    if level:
        needle = level.strip().lower()
        filtered = [r for r in filtered if str(r.get("level", "")).strip().lower() == needle]

    return {
        "documentTitle": payload.get("documentTitle"),
        "exportedAtUtc": payload.get("exportedAtUtc"),
        "matchCount": len(filtered),
        "rooms": filtered,
    }


QUERY_ROOM_DATA_TOOL = {
    "type": "function",
    "function": {
        "name": "query_room_data",
        "description": (
            "Query extracted BIM room data from the local Revit export. "
            "Use this for questions about rooms, areas, levels, doors, or windows."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "room_number": {
                    "type": "string",
                    "description": "Optional room number filter, e.g. '101'.",
                },
                "level": {
                    "type": "string",
                    "description": "Optional level name filter, e.g. 'Level 1'.",
                },
            },
            "additionalProperties": False,
        },
    },
}
