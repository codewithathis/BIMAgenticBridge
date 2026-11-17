# Installer (Inno Setup 6)

Builds `dist/BIMAgenticBridge-Setup-{version}.exe` for end users.

## Prerequisites (packager machine)

- Windows x64
- Autodesk Revit **2027** (for compiling the plugin against RevitAPI)
- .NET **10** SDK (x64)
- Python 3.11+ with backend venv (`backend/.venv`)
- [Inno Setup 6](https://jrsoftware.org/isinfo.php) (`ISCC.exe`)
- Close Revit before packaging (DLL lock)
- **Windows Defender:** unsigned PyInstaller bootloaders are often quarantined immediately. Add exclusions for `dist\` and `build\pyinstaller\` (or restore the quarantined `BimAgenticBridge.Backend.exe`) before packaging. If the EXE is missing, `build-backend-exe.ps1` falls back to an embeddable CPython portable bundle + `.cmd` launcher.

## One-shot package

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package-release.ps1
```

Outputs:

- `dist/payload/Plugin/` — add-in DLLs
- `dist/payload/Backend/` — PyInstaller one-folder freeze
- `dist/BIMAgenticBridge-Setup-{version}.exe`

Partial rebuilds:

```powershell
.\scripts\package-release.ps1 -SkipBackend
.\scripts\package-release.ps1 -SkipPlugin
.\scripts\package-release.ps1 -SkipInno
```

## Clean-machine test checklist

On a Windows VM **without** Python or the .NET SDK (Revit 2027 installed):

1. Run Setup.exe (Revit 2027 must be detected, or `/SkipRevitCheck=1` for labs only).
2. Optionally enter an API key; or skip and use Start Menu → **Configure API Key**.
3. Confirm `%LOCALAPPDATA%\BimAgenticBridge\config.json` exists (`require_auth`, `auth_token`).
4. Confirm credentials are in `credentials.dat` (not plaintext in Program Files).
5. Start Menu → **Start Backend** → `http://127.0.0.1:8000/health` returns product `BIM Agentic Bridge`.
6. Open Revit 2027 → **BIM Agentic** → **AI Chat** → ask a room question.
7. Open a second Revit instance; chat still works; close the first instance; second still works.
8. Put a foreign listener on port 8000; confirm the plugin does **not** kill it and shows a clear error.
9. Reinstall Setup.exe; credentials/config preserved.
10. Uninstall; `.addin` and Program Files removed; choose whether to delete user data when prompted.

## GitHub Releases

1. Bump [`version.txt`](../version.txt)
2. Run `package-release.ps1`
3. Create a GitHub Release and upload `BIMAgenticBridge-Setup-*.exe`
4. Paste clean-machine notes in the release body

## Code signing (P2 — commercial)

Before wide distribution, Authenticode-sign:

- `BimAgenticBridge.dll`
- `BimAgenticBridge.Backend.exe`
- `BIMAgenticBridge-Setup-*.exe`

Use your org’s certificate (DigiCert, Sectigo, etc.). Unsigned installers trigger SmartScreen warnings.

## Advanced install flags

| Flag | Meaning |
|------|---------|
| `/SkipRevitCheck=1` | Allow install without detecting Revit 2027 (dev/lab only) |
| `/SILENT` | Unattended Inno install |
