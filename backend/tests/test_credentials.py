from pathlib import Path

from app.credentials import Credentials, load_credentials, save_credentials


def test_credentials_roundtrip_plain_marker(tmp_path: Path, monkeypatch) -> None:
    # Force non-DPAPI path used on non-Windows; on Windows still OK via roundtrip APIs.
    path = tmp_path / "credentials.dat"
    creds = Credentials(
        llm_provider="gemini",
        gemini_api_key="secret-key",
        openai_api_key="",
    )
    save_credentials(creds, path)
    loaded = load_credentials(path)
    assert loaded is not None
    assert loaded.gemini_api_key == "secret-key"
    assert loaded.has_usable_key() is True
