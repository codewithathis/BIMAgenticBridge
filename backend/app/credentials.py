"""DPAPI-protected credentials for installed backends; .env remains a dev fallback."""

from __future__ import annotations

import base64
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.paths import credentials_dat_path, ensure_local_app_data


@dataclass
class Credentials:
    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    openai_model: str = "gpt-4o-mini"

    def to_dict(self) -> dict[str, str]:
        return {
            "llm_provider": self.llm_provider,
            "gemini_api_key": self.gemini_api_key,
            "openai_api_key": self.openai_api_key,
            "gemini_model": self.gemini_model,
            "openai_model": self.openai_model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Credentials":
        raw = data or {}
        return cls(
            llm_provider=str(raw.get("llm_provider") or "gemini").strip() or "gemini",
            gemini_api_key=str(raw.get("gemini_api_key") or "").strip(),
            openai_api_key=str(raw.get("openai_api_key") or "").strip(),
            gemini_model=str(raw.get("gemini_model") or "gemini-1.5-flash").strip()
            or "gemini-1.5-flash",
            openai_model=str(raw.get("openai_model") or "gpt-4o-mini").strip()
            or "gpt-4o-mini",
        )

    def has_usable_key(self) -> bool:
        provider = (self.llm_provider or "gemini").strip().lower()
        if provider in ("openai", "gpt"):
            return bool(self.openai_api_key)
        return bool(self.gemini_api_key)


def _dpapi_protect(plain: bytes) -> bytes:
    if sys.platform != "win32":
        # Non-Windows: store base64 of plaintext with a marker (dev only).
        return b"PLAIN:" + base64.b64encode(plain)

    import ctypes
    import ctypes.wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", ctypes.wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    buffer = ctypes.create_string_buffer(plain)
    blob_in = DATA_BLOB(len(plain), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()

    if not crypt32.CryptProtectData(
        ctypes.byref(blob_in),
        "BimAgenticBridge",
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    ):
        raise OSError("CryptProtectData failed")

    try:
        protected = ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        kernel32.LocalFree(blob_out.pbData)
    return protected


def _dpapi_unprotect(protected: bytes) -> bytes:
    if protected.startswith(b"PLAIN:"):
        return base64.b64decode(protected[6:])

    if sys.platform != "win32":
        raise OSError("DPAPI credentials can only be decrypted on Windows")

    import ctypes
    import ctypes.wintypes

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", ctypes.wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    buffer = ctypes.create_string_buffer(protected)
    blob_in = DATA_BLOB(len(protected), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()

    if not crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(blob_out),
    ):
        raise OSError("CryptUnprotectData failed")

    try:
        return ctypes.string_at(blob_out.pbData, blob_out.cbData)
    finally:
        kernel32.LocalFree(blob_out.pbData)


def save_credentials(credentials: Credentials, path: Path | None = None) -> Path:
    ensure_local_app_data()
    target = path or credentials_dat_path()
    payload = json.dumps(credentials.to_dict()).encode("utf-8")
    protected = _dpapi_protect(payload)
    target.write_bytes(protected)
    return target


def load_credentials(path: Path | None = None) -> Credentials | None:
    target = path or credentials_dat_path()
    if not target.is_file():
        return None
    try:
        plain = _dpapi_unprotect(target.read_bytes())
        data = json.loads(plain.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return Credentials.from_dict(data)


def apply_credentials_to_environ(credentials: Credentials) -> None:
    """Inject secrets into process env for Settings / LLM clients (never log these)."""
    if credentials.llm_provider:
        os.environ["LLM_PROVIDER"] = credentials.llm_provider
    if credentials.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = credentials.gemini_api_key
    if credentials.openai_api_key:
        os.environ["OPENAI_API_KEY"] = credentials.openai_api_key
    if credentials.gemini_model:
        os.environ["GEMINI_MODEL"] = credentials.gemini_model
    if credentials.openai_model:
        os.environ["OPENAI_MODEL"] = credentials.openai_model


def load_and_apply_credentials() -> Credentials | None:
    creds = load_credentials()
    if creds is not None:
        apply_credentials_to_environ(creds)
    return creds
