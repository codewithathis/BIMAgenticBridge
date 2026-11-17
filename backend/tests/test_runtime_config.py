import json
from pathlib import Path

from app.runtime_config import RuntimeConfig, ensure_runtime_config, load_runtime_config, save_runtime_config


def test_ensure_runtime_config_creates_token(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    cfg = ensure_runtime_config(path)
    assert cfg.auth_token
    assert path.is_file()
    again = load_runtime_config(path)
    assert again.auth_token == cfg.auth_token


def test_save_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    cfg = RuntimeConfig(
        install_dir=r"C:\Program Files\BimAgenticBridge",
        api_base_url="http://127.0.0.1:8000",
        auth_token="test-token",
        require_auth=True,
        version="1.0.0",
    )
    save_runtime_config(cfg, path)
    loaded = load_runtime_config(path)
    assert loaded.install_dir == cfg.install_dir
    assert loaded.auth_token == "test-token"
    assert loaded.require_auth is True
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "auth_token" in data
