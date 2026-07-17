# BimAgenticBridge

AI-based BIM assessment bridge: a Revit 2024 WPF chat plugin that exports room data, plus a local FastAPI agent that answers questions using OpenAI tool-calling against the exported JSON.

## Architecture

```
Revit WPF Chat  →  POST /chat  →  OpenAI tools agent
       ↑                              │
       │                     query_room_data tool
       │                              ↓
  FilteredElementCollector → %LOCALAPPDATA%\BimAgenticBridge\data.json
```

When the agent needs room data and the JSON is missing or stale, it returns `extraction_required`. The plugin extracts rooms on the Revit API thread, writes `data.json`, and retries with `data_ready: true`.

## Repository layout

| Path | Purpose |
|------|---------|
| `revit-plugin/` | C# .NET Framework 4.8 Revit add-in |
| `backend/` | FastAPI agent (`POST /chat`) |
| `data/` | Placeholder (runtime export uses AppData) |

Shared data path (both sides):

`%LOCALAPPDATA%\BimAgenticBridge\data.json`

## Backend setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and set `OPENAI_API_KEY`. Then:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check: `GET http://127.0.0.1:8000/health`

## Revit plugin setup

1. Restore Newtonsoft.Json (see [revit-plugin/README.md](revit-plugin/README.md))
2. Open `revit-plugin/BimAgenticBridge.sln` in Visual Studio 2022
3. Confirm Revit 2024 DLL HintPaths in the `.csproj`
4. Build Debug
5. Copy `revit-plugin/BimAgenticBridge.addin` to `%AppData%\Autodesk\Revit\Addins\2024\`
6. Edit `<Assembly>` in the `.addin` file to your built `BimAgenticBridge.dll` path
7. Ensure `Newtonsoft.Json.dll` sits next to the plugin DLL
8. Start Revit 2024 → ribbon tab **BimAgenticBridge** → **Chat**

## Chat API contract

`POST /chat`

```json
{ "message": "How many doors in room 101?", "force_extract": false, "data_ready": false }
```

| status | meaning |
|--------|---------|
| `ok` | `reply` contains the natural-language answer |
| `extraction_required` | Plugin must export rooms, then retry with `data_ready: true` |

## Test plan

Use this checklist before submission.

### A. Plugin load

1. Place `.addin` + build output; start Revit 2024
2. Confirm no add-in error dialog; ribbon button **BimAgenticBridge** appears
3. Click **Chat** → dockable chat panel opens

### B. Extraction only

1. Open a model with several rooms, doors, and windows
2. Ask a room question so the backend returns `extraction_required` (or delete `data.json` first)
3. Confirm `%LOCALAPPDATA%\BimAgenticBridge\data.json` is created
4. Spot-check one room: Name, Number, Level, Area, door/window counts vs Revit

### C. Backend without Revit

1. Copy `backend/tests/fixtures/sample_rooms.json` to `%LOCALAPPDATA%\BimAgenticBridge\data.json`
2. Set `OPENAI_API_KEY` in `backend/.env`
3. Start uvicorn on port 8000
4. `POST /chat` with `"List rooms on Level 1"` → answer grounded in JSON
5. Delete `data.json` → BIM question returns `extraction_required` (not a hallucinated inventory)

### D. End-to-end

1. Revit + backend both running
2. Ask: “How many windows in room 101?”
3. Expect extract if needed → JSON update → NL answer matching the model
4. Ask a non-BIM question (“What is BIM?”) → answer without forcing extract

### E. Automated backend tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

### F. Maintainability smoke

1. Change TTL / path only in `backend/.env` (`DATA_TTL_SECONDS`, `DATA_JSON_PATH`)
2. Confirm extractor (`RoomExtractor`) and API client (`ChatApiClient`) remain independent modules

## Configuration reference

| Variable | Default | Notes |
|----------|---------|-------|
| `OPENAI_API_KEY` | _(empty)_ | Required for `/chat` |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model |
| `DATA_JSON_PATH` | `%LOCALAPPDATA%\BimAgenticBridge\data.json` | Must match plugin |
| `DATA_TTL_SECONDS` | `300` | Stale threshold before re-extract |
