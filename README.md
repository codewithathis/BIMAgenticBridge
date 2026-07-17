# BIM Agentic Bridge

AI-based BIM assessment bridge: a **Revit 2027** (.NET 10) WPF chat plugin that exports room data, plus a local **FastAPI** agent that answers questions using OpenAI tool-calling against the exported JSON.

## Author

**Athis J**

| | |
|---|---|
| Email | [trichyathis@gmail.com](mailto:trichyathis@gmail.com) |
| GitHub | [github.com/codewithathis](https://github.com/codewithathis) |
| LinkedIn | [linkedin.com/in/athis-j](https://www.linkedin.com/in/athis-j) |

See also [AUTHORS.md](AUTHORS.md).

---

## For recruiters / reviewers — run it yourself

You can evaluate this project without the author’s machine. You need:

| Requirement | Notes |
|-------------|--------|
| Windows 10/11 | Revit is Windows-only |
| Autodesk Revit **2027** | API DLLs + runtime host |
| .NET **10** SDK (x64) | `C:\Program Files\dotnet\dotnet.exe --list-sdks` |
| Python **3.11+** | Backend agent |
| OpenAI API key | Your own key in `backend/.env` |

### 1) Backend (5 minutes)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`:

- Set `OPENAI_API_KEY`
- Leave `DATA_JSON_PATH` empty (uses `%LOCALAPPDATA%\BimAgenticBridge\data.json`)

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Checks:

- `GET http://127.0.0.1:8000/health` → `{"status":"ok"}`
- `GET http://127.0.0.1:8000/about` → author credits
- Optional (no Revit): copy `backend/tests/fixtures/sample_rooms.json` to `%LOCALAPPDATA%\BimAgenticBridge\data.json`, then `POST /chat` with a room question

```powershell
pytest
```

### 2) Revit plugin

1. Set your Revit install path when building if it is not `D:\Development\Autodesk\Revit 2027`:

```powershell
& "C:\Program Files\dotnet\dotnet.exe" build revit-plugin\BimAgenticBridge.sln -c Debug `
  -p:RevitInstallPath="C:\Program Files\Autodesk\Revit 2027"
```

2. Install the add-in for your user profile:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-addin.ps1
```

3. Start **Revit 2027** → ribbon **BIM Agentic** → **AI Chat**
4. Open an **Architectural** model with rooms (Snowdon sample):  
   `...\Revit 2027\Samples\Snowdon Towers Sample Architectural.rvt`  
   (The Structural sample has no rooms — that is expected.)
5. With the backend running, ask: `How many rooms are on Level 1?`

Shared export path (plugin + API):

`%LOCALAPPDATA%\BimAgenticBridge\data.json`

---

## Architecture

```
Revit WPF Chat  →  POST /chat  →  OpenAI tools agent
       ↑                              │
       │                     query_room_data tool
       │                              ↓
  FilteredElementCollector → %LOCALAPPDATA%\BimAgenticBridge\data.json
```

When the agent needs room data and the JSON is missing or stale, it returns `extraction_required`. The plugin extracts on the Revit API thread, writes `data.json`, and retries with `data_ready: true`.

## Repository layout

| Path | Purpose |
|------|---------|
| `revit-plugin/` | C# .NET 10 Revit 2027 add-in |
| `backend/` | FastAPI agent (`POST /chat`) |
| `scripts/install-addin.ps1` | One-step add-in install for reviewers |
| `AUTHORS.md` | Author credits |
| `data/` | Placeholder (runtime export uses AppData) |

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

### A. Plugin load

1. Run `scripts/install-addin.ps1`; start Revit 2027
2. Ribbon tab **BIM Agentic** → **AI Chat** appears
3. Dockable panel **BIM Agentic Bridge** opens (footer credits the author)

### B. Extraction

1. Open **Snowdon Towers Sample Architectural.rvt**
2. Ask a room question (or delete `data.json` first)
3. Confirm `%LOCALAPPDATA%\BimAgenticBridge\data.json` has `roomCount` greater than 0
4. Spot-check Name, Number, Level, Area, door/window counts vs Revit

### C. Backend without Revit

1. Copy fixture JSON to the AppData path
2. Set `OPENAI_API_KEY`; start uvicorn
3. `POST /chat` → answer grounded in JSON
4. Delete `data.json` → BIM question returns `extraction_required`

### D. End-to-end

1. Revit + backend running
2. Ask about windows/doors in a known room
3. Ask a non-BIM question → no forced extract

## Configuration reference

| Variable | Default | Notes |
|----------|---------|-------|
| `OPENAI_API_KEY` | _(empty)_ | Required for `/chat` |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chat model |
| `DATA_JSON_PATH` | `%LOCALAPPDATA%\BimAgenticBridge\data.json` | Must match plugin |
| `DATA_TTL_SECONDS` | `300` | Stale threshold before re-extract |

## Credits

Developed by **[Athis J](https://github.com/codewithathis)** for technical assessment / portfolio demonstration.  
Contact: [trichyathis@gmail.com](mailto:trichyathis@gmail.com) · [LinkedIn](https://www.linkedin.com/in/athis-j)
