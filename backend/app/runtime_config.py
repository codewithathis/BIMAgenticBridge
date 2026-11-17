"""Load/save %LOCALAPPDATA%\\BimAgenticBridge\\config.json."""

from __future__ import annotations

import json
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.paths import config_json_path, ensure_local_app_data


@dataclass
class RuntimeConfig:
    install_dir: str = ""
    api_base_url: str = "http://127.0.0.1:8000"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    auth_token: str = ""
    version: str = "1.0.0"
    backend_exe_path: str = ""
    # Installer sets true; plain source checkouts stay false until configured.
    require_auth: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "RuntimeConfig":
        raw = data or {}
        port = raw.get("api_port", 8000)
        try:
            port_int = int(port)
        except (TypeError, ValueError):
            port_int = 8000

        host = str(raw.get("api_host") or "127.0.0.1").strip() or "127.0.0.1"
        base = str(raw.get("api_base_url") or "").strip()
        if not base:
            base = f"http://{host}:{port_int}"

        return cls(
            install_dir=str(raw.get("install_dir") or ""),
            api_base_url=base.rstrip("/"),
            api_host=host,
            api_port=port_int,
            auth_token=str(raw.get("auth_token") or ""),
            version=str(raw.get("version") or "1.0.0"),
            backend_exe_path=str(raw.get("backend_exe_path") or ""),
            require_auth=bool(raw.get("require_auth", True)),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_runtime_config(path: Path | None = None) -> RuntimeConfig:
    cfg_path = path or config_json_path()
    if not cfg_path.is_file():
        return RuntimeConfig()
    try:
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return RuntimeConfig()
    if not isinstance(data, dict):
        return RuntimeConfig()
    return RuntimeConfig.from_dict(data)


def save_runtime_config(config: RuntimeConfig, path: Path | None = None) -> Path:
    ensure_local_app_data()
    cfg_path = path or config_json_path()
    cfg_path.write_text(
        json.dumps(config.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    return cfg_path


def ensure_runtime_config(path: Path | None = None) -> RuntimeConfig:
    """Load config.json, generating an auth token on first run if missing."""
    cfg = load_runtime_config(path)
    changed = False
    if not cfg.auth_token:
        cfg.auth_token = secrets.token_urlsafe(32)
        changed = True
    if cfg.api_host not in ("127.0.0.1", "localhost"):
        # Hard rule: never bind/advertise non-loopback by default.
        cfg.api_host = "127.0.0.1"
        cfg.api_base_url = f"http://127.0.0.1:{cfg.api_port}"
        changed = True
    if changed:
        save_runtime_config(cfg, path)
    return cfg
