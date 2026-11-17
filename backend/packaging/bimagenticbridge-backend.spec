# -*- mode: python ; coding: utf-8 -*-
# PyInstaller one-folder spec for BIM Agentic Bridge backend (Windows x64).
# Build via: scripts/build-backend-exe.ps1

import sys
from pathlib import Path

block_cipher = None
backend_root = Path(SPECPATH).resolve().parent
run_server = backend_root / "run_server.py"
datas = []
certifi_datas = []
try:
    import certifi
    certifi_datas = [(certifi.where(), "certifi")]
except Exception:
    pass

hiddenimports = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "starlette",
    "pydantic",
    "pydantic_settings",
    "pydantic_core",
    "anyio",
    "httpx",
    "httpcore",
    "dotenv",
    "google.genai",
    "google.adk",
    "google.auth",
    "openai",
    "certifi",
    "app",
    "app.main",
    "app.config",
    "app.auth",
    "app.credentials",
    "app.runtime_config",
    "app.paths",
    "app.routers.chat",
    "app.agent",
    "app.llm",
    "app.gemini_client",
    "app.openai_client",
    "app.adk_agent",
    "app.services.tool_loop",
    "app.services.openai_loop",
    "app.services.tool_executor",
    "app.services.data_readiness",
    "app.tools.room_query",
]

a = Analysis(
    [str(run_server)],
    pathex=[str(backend_root)],
    binaries=[],
    datas=certifi_datas + [
        (str(backend_root / "data"), "data"),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytest_asyncio"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BimAgenticBridge.Backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Backend",
)
