import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_json_path() -> str:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return str(Path(local_app_data) / "BimAgenticBridge" / "data.json")
    return str(Path.home() / "AppData" / "Local" / "BimAgenticBridge" / "data.json")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    google_cloud_project: str = ""
    google_cloud_location: str = "us-central1"
    google_genai_use_vertexai: bool = False
    data_json_path: str = ""
    data_ttl_seconds: int = 300
    api_host: str = "127.0.0.1"
    api_port: int = 8000

    @property
    def resolved_data_json_path(self) -> Path:
        if self.data_json_path:
            path = Path(os.path.expandvars(self.data_json_path)).expanduser()
            if not path.is_absolute():
                # Resolve relative paths from the backend working directory.
                path = (Path.cwd() / path).resolve()
            return path
        return Path(default_data_json_path())


@lru_cache
def get_settings() -> Settings:
    return Settings()
