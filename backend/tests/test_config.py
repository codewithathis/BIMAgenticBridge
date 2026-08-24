import os
from unittest.mock import patch

from app.config import Settings, bundled_data_json_path, default_data_json_path


def test_bundled_snapshot_exists() -> None:
    assert bundled_data_json_path().is_file()


def test_vercel_uses_bundled_data_json() -> None:
    with patch.dict(os.environ, {"VERCEL": "1"}, clear=False):
        assert default_data_json_path() == bundled_data_json_path()
        settings = Settings(data_json_path="")
        assert settings.resolved_data_json_path == bundled_data_json_path()
