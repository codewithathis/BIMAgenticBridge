"""Shared LocalAppData paths for installed and development backends."""

from __future__ import annotations

import os
from pathlib import Path

APP_FOLDER_NAME = "BimAgenticBridge"
PRODUCT_NAME = "BIM Agentic Bridge"
PRODUCT_SLUG = "bim-agentic-bridge"


def local_app_data_root() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / APP_FOLDER_NAME
    return Path.home() / "AppData" / "Local" / APP_FOLDER_NAME


def ensure_local_app_data() -> Path:
    root = local_app_data_root()
    root.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(parents=True, exist_ok=True)
    return root


def config_json_path() -> Path:
    return local_app_data_root() / "config.json"


def credentials_dat_path() -> Path:
    return local_app_data_root() / "credentials.dat"


def backend_pid_path() -> Path:
    return local_app_data_root() / "backend.pid"


def backend_log_path() -> Path:
    return local_app_data_root() / "logs" / "backend.log"


def data_json_path() -> Path:
    return local_app_data_root() / "data.json"
