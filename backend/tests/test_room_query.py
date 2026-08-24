from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.tools.room_query import check_data_availability, query_room_data


def test_query_all_rooms(sample_rooms_path: Path) -> None:
    result = query_room_data(sample_rooms_path)
    assert result["matchCount"] == 3
    assert result["documentTitle"] == "Sample.rvt"
    assert result["levelCount"] == 2
    assert result["roomCountTotal"] == 3


def test_query_filter_by_room_number(sample_rooms_path: Path) -> None:
    result = query_room_data(sample_rooms_path, room_number="101")
    assert result["matchCount"] == 1
    assert result["rooms"][0]["name"] == "Office"
    assert result["rooms"][0]["doorCount"] == 2


def test_query_filter_by_level(sample_rooms_path: Path) -> None:
    result = query_room_data(sample_rooms_path, level="Level 2")
    assert result["matchCount"] == 1
    assert result["rooms"][0]["number"] == "201"


def test_missing_data_file(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    availability = check_data_availability(missing, ttl_seconds=300)
    assert availability.exists is False
    assert availability.stale is True


def test_fresh_data_not_stale(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    exported = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path.write_text(
        f'{{"exportedAtUtc": "{exported}", "documentTitle": "T", "rooms": []}}',
        encoding="utf-8",
    )
    availability = check_data_availability(path, ttl_seconds=300)
    assert availability.exists is True
    assert availability.stale is False


def test_stale_data_detected(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    exported = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat().replace(
        "+00:00", "Z"
    )
    path.write_text(
        f'{{"exportedAtUtc": "{exported}", "documentTitle": "T", "rooms": []}}',
        encoding="utf-8",
    )
    availability = check_data_availability(path, ttl_seconds=60)
    assert availability.exists is True
    assert availability.stale is True


def test_zero_ttl_never_stale(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    exported = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
    path.write_text(
        f'{{"exportedAtUtc": "{exported}", "documentTitle": "T", "rooms": []}}',
        encoding="utf-8",
    )
    availability = check_data_availability(path, ttl_seconds=0)
    assert availability.exists is True
    assert availability.stale is False
