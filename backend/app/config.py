import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.paths import data_json_path, local_app_data_root
from app.runtime_config import ensure_runtime_config


def bundled_data_json_path() -> Path:
    """Snapshot shipped with the backend (used on Vercel and as a local fallback)."""
    return Path(__file__).resolve().parent.parent / "data" / "data.json"


def default_data_json_path() -> Path:
    bundled = bundled_data_json_path()
    if os.environ.get("VERCEL"):
        return bundled

    local = data_json_path()
    if local.exists() or not bundled.exists():
        return local
    return bundled


def _env_files() -> tuple[str, ...]:
    """Prefer LocalAppData .env for installed apps; keep cwd .env for developers."""
    files: list[str] = []
    local_env = local_app_data_root() / ".env"
    if local_env.is_file():
        files.append(str(local_env))
    files.append(".env")
    return tuple(files)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_files(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    google_genai_use_vertexai: bool = False
    data_json_path: str = ""
    data_ttl_seconds: int = 300
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    # Populated from config.json at process start; empty disables auth (dev/Vercel).
    auth_token: str = ""
    require_auth: bool = False
    product_version: str = "1.0.0"

    @property
    def resolved_data_json_path(self) -> Path:
        if self.data_json_path:
            path = Path(os.path.expandvars(self.data_json_path)).expanduser()
            if not path.is_absolute():
                path = (Path.cwd() / path).resolve()
            return path
        return default_data_json_path()


def bootstrap_settings_from_runtime() -> None:
    """Apply LocalAppData config.json + DPAPI credentials before Settings is cached."""
    from app.credentials import load_and_apply_credentials

    load_and_apply_credentials()
    if os.environ.get("VERCEL"):
        return

    cfg = ensure_runtime_config()
    # Force loopback for local installs.
    host = cfg.api_host if cfg.api_host in ("127.0.0.1", "localhost") else "127.0.0.1"
    os.environ.setdefault("API_HOST", host)
    os.environ.setdefault("API_PORT", str(cfg.api_port))
    if cfg.auth_token:
        os.environ["AUTH_TOKEN"] = cfg.auth_token
    installed = bool(cfg.install_dir or cfg.backend_exe_path or cfg.require_auth)
    os.environ["REQUIRE_AUTH"] = "true" if installed and cfg.auth_token else "false"
    if cfg.version:
        os.environ.setdefault("PRODUCT_VERSION", cfg.version)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
