from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.exceptions import ExtractionRequired
from app.services.data_readiness import DataReadinessPolicy


def test_force_extract_required() -> None:
    policy = DataReadinessPolicy(Path("unused.json"), ttl_seconds=300)
    assert policy.force_extract_required(data_ready=False, force_extract=True) is not None
    assert policy.force_extract_required(data_ready=True, force_extract=True) is None


def test_missing_file_requires_extraction(tmp_path: Path) -> None:
    policy = DataReadinessPolicy(tmp_path / "missing.json", ttl_seconds=300)
    with pytest.raises(ExtractionRequired, match="missing"):
        policy.ensure_ready(data_ready=False)


def test_missing_after_client_extract_still_fails(tmp_path: Path) -> None:
    policy = DataReadinessPolicy(tmp_path / "missing.json", ttl_seconds=300)
    with pytest.raises(ExtractionRequired, match="still missing"):
        policy.ensure_ready(data_ready=True)


def test_fresh_file_is_ready(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    exported = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    path.write_text(
        f'{{"exportedAtUtc": "{exported}", "documentTitle": "T", "rooms": []}}',
        encoding="utf-8",
    )
    policy = DataReadinessPolicy(path, ttl_seconds=300)
    policy.ensure_ready(data_ready=False)


def test_stale_file_requires_extraction(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    exported = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat().replace(
        "+00:00", "Z"
    )
    path.write_text(
        f'{{"exportedAtUtc": "{exported}", "documentTitle": "T", "rooms": []}}',
        encoding="utf-8",
    )
    policy = DataReadinessPolicy(path, ttl_seconds=60)
    with pytest.raises(ExtractionRequired, match="stale"):
        policy.ensure_ready(data_ready=False)


def test_stale_allowed_when_data_ready(tmp_path: Path) -> None:
    path = tmp_path / "data.json"
    exported = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat().replace(
        "+00:00", "Z"
    )
    path.write_text(
        f'{{"exportedAtUtc": "{exported}", "documentTitle": "T", "rooms": []}}',
        encoding="utf-8",
    )
    policy = DataReadinessPolicy(path, ttl_seconds=60)
    policy.ensure_ready(data_ready=True)
