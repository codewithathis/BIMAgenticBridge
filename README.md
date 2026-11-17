# BIM Agentic Bridge

**Ask your Revit model questions in plain English — get answers grounded in live BIM data.**

BIM Agentic Bridge is an AI-powered Revit plugin that turns room, level, door, and window data into a conversational assistant inside Autodesk Revit. Architects, BIM managers, and project teams can query the active model without building schedules or exporting spreadsheets first.

BIM Agentic Bridge in Autodesk Revit — chat answering “how many rooms available” with 113 rooms

*Demo: docked **BIM Agentic Bridge** chat in Revit 2027, answering natural-language questions from extracted model data.*

---



## Product overview


|              |                                                                                                         |
| ------------ | ------------------------------------------------------------------------------------------------------- |
| **Product**  | BIM Agentic Bridge                                                                                      |
| **Platform** | Autodesk Revit 2027 (.NET 10 add-in) + FastAPI Gemini agent (local / Cloud Run)                         |
| **Author**   | [Athis J](https://github.com/codewithathis)                                                             |
| **Contact**  | [trichyathis@gmail.com](mailto:trichyathis@gmail.com) · [LinkedIn](https://www.linkedin.com/in/athis-j) |




### What it does

1. **Chat inside Revit** — Dockable WPF panel on the **BIM Agentic** ribbon tab.
2. **Extract model data** — Uses the Revit API (`FilteredElementCollector`) to export rooms (name, number, level, area), door/window counts, and levels — including loaded linked models.
3. **Answer with AI tools** — A FastAPI agent uses Gemini function calling (Google GenAI SDK / ADK) to query the export and reply in natural language.
4. **Stay in sync** — If data is missing or stale, the agent requests a fresh extraction; the plugin refreshes and retries automatically (with timeout protection).



### Who it is for

- Architecture / interior firms using Revit daily  
- BIM managers validating room inventories and openings  
- Design QA / assessment workflows (“how many rooms?”, “doors on Level 2?”)  
- Consultancies pitching AI + BIM productivity tools



### Key benefits

- **Faster answers** — No schedule setup for common room questions  
- **Grounded in the model** — Answers come from extracted JSON, not invented counts  
- **In-context UX** — Chat stays docked next to the 3D/plan view  
- **Local-first agent** — Backend runs on your machine or Cloud Run; you control the Gemini key / GCP credentials  
- **Extensible** — Tool-based agent design can grow to more BIM queries



### Example questions

- How many rooms are available?  
- How many rooms are on Level 1?  
- How many doors / windows in room 101?  
- List levels in this model  
- Which rooms have no windows?

---



## Architecture

```
Revit WPF Chat  →  POST /chat  →  Gemini / ADK tools agent
       ↑                              │
       │                     query_room_data tool
       │                              ↓
  FilteredElementCollector → %LOCALAPPDATA%\BimAgenticBridge\data.json
```

When the agent needs room data and the JSON is missing or stale, it returns `extraction_required`. The plugin extracts on the Revit API thread (45s timeout), writes `data.json`, and retries with `data_ready: true`.

Backend collaborators: `DataReadinessPolicy`, `ToolExecutor`, and `ToolLoop` (orchestrated by `ChatAgent`).

### Design patterns

Client–server · MVVM · Command · Agent + Tools · DTO · ExternalEvent marshaling · layered modules  

---



## Commercial / licensing inquiry

For pilots, licensing, or custom features (more element categories, company branding, multi-version Revit support, on-prem LLM), contact:

**Athis J** — [trichyathis@gmail.com](mailto:trichyathis@gmail.com) · [GitHub](https://github.com/codewithathis) · [LinkedIn](https://www.linkedin.com/in/athis-j)

---



## Support

If this project helped you, you can [buy me a coffee](https://buymeacoffee.com/codewithathis).

---



## Install (end users)

| Requirement | Notes |
| --- | --- |
| Windows 10/11 x64 | Revit is Windows-only |
| Autodesk Revit **2027** | Detected by the installer |
| Gemini or OpenAI API key | Optional during setup; configure later from Start Menu |

1. Download `BIMAgenticBridge-Setup-*.exe` from [GitHub Releases](https://github.com/codewithathis/BimAgenticBridge/releases).
2. Run the installer (no Python or .NET SDK required).
3. Optionally enter your API key (stored with Windows DPAPI under `%LOCALAPPDATA%\BimAgenticBridge`).
4. Open **Revit 2027** → ribbon **BIM Agentic** → **AI Chat**.
5. Ask: `How many rooms are available?`

Start Menu shortcuts: **Start Backend**, **Stop Backend**, **Configure API Key**.  
The local backend listens on `http://127.0.0.1:8000` and stays running after Revit closes so multiple Revit sessions can share it.

Packaging / signing notes for maintainers: [`installer/README.md`](installer/README.md).

---

## For developers — run from source


| Requirement                 | Notes                                                     |
| --------------------------- | --------------------------------------------------------- |
| Windows 10/11               | Revit is Windows-only                                     |
| Autodesk Revit **2027**     | API DLLs + runtime host                                   |
| .NET **10** SDK (x64)       | `C:\Program Files\dotnet\dotnet.exe --list-sdks`          |
| Python **3.11+**            | Backend agent                                             |
| Gemini API key (or GCP ADC) | Your own key in `backend/.env`, or Vertex AI on Cloud Run |



### 1) Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`: set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`, or `LLM_PROVIDER=openai` and `OPENAI_API_KEY`. Leave `DATA_JSON_PATH` empty for `%LOCALAPPDATA%\BimAgenticBridge\data.json`.

```powershell
# Dev (uvicorn)
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Or the packaging entrypoint
python run_server.py
```

- Health: `GET http://127.0.0.1:8000/health` (includes `product` + `version`)  
- About: `GET http://127.0.0.1:8000/about`  
- Tests: `pytest`

Public URL without GCP billing (Vercel): set Root Directory to `backend`, add `LLM_PROVIDER` and `GEMINI_API_KEY` in Vercel env vars, then `cd backend && npx vercel --prod`. The deploy includes `backend/data/data.json`. Details in `backend/README.md`.



### 2) Revit plugin

```powershell
# Close Revit first (it locks the DLL)
powershell -ExecutionPolicy Bypass -File .\scripts\build-plugin.ps1
```

Or build manually, then:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-addin.ps1
```

1. Start **Revit 2027** → **BIM Agentic** → **AI Chat**
2. Open an **Architectural** model with rooms (e.g. Snowdon Towers Sample Architectural)
3. Ask: `How many rooms are available?`

Shared path: `%LOCALAPPDATA%\BimAgenticBridge\data.json`

### 3) Build the Windows installer

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\package-release.ps1
```

Produces `dist/BIMAgenticBridge-Setup-{version}.exe`. See [`installer/README.md`](installer/README.md).

---



## Repository layout


| Path                            | Purpose                                      |
| ------------------------------- | -------------------------------------------- |
| `revit-plugin/`                 | C# .NET 10 Revit 2027 add-in                 |
| `backend/`                      | FastAPI agent (`POST /chat`)                 |
| `backend/run_server.py`         | Local/frozen backend entrypoint              |
| `installer/`                    | Inno Setup script + install helpers          |
| `scripts/build-plugin.ps1`      | Build + install add-in (dev)                 |
| `scripts/build-backend-exe.ps1` | PyInstaller one-folder freeze                |
| `scripts/package-release.ps1`   | Full Setup.exe packaging                     |
| `scripts/install-addin.ps1`     | Write `.addin` for Revit 2027                |
| `version.txt`                   | Product version for releases                 |
| `Screenshot_1.png`              | Product screenshot                           |
| `AUTHORS.md`                    | Author credits                               |




## Chat API contract

`POST /chat`

```json
{ "message": "How many doors in room 101?", "force_extract": false, "data_ready": false }
```


| status                | meaning                                                |
| --------------------- | ------------------------------------------------------ |
| `ok`                  | Natural-language answer in `reply`                     |
| `extraction_required` | Plugin must export, then retry with `data_ready: true` |

Installed backends also require header `X-BimAgentic-Token` (from `%LOCALAPPDATA%\BimAgenticBridge\config.json`).



## Configuration


| Variable                    | Default                                     | Notes                                           |
| --------------------------- | ------------------------------------------- | ----------------------------------------------- |
| `LLM_PROVIDER`              | `gemini`                                    | `gemini` or `openai`                            |
| `GEMINI_API_KEY`            | *(empty)*                                   | Required when `LLM_PROVIDER=gemini` unless ADC  |
| `GEMINI_MODEL`              | `gemini-1.5-flash`                          | Gemini chat model                               |
| `OPENAI_API_KEY`            | *(empty)*                                   | Required when `LLM_PROVIDER=openai`             |
| `OPENAI_MODEL`              | `gpt-4o-mini`                               | OpenAI chat model                               |
| `GOOGLE_GENAI_USE_VERTEXAI` | `false`                                     | Use Vertex AI + Application Default Credentials |
| `GOOGLE_CLOUD_PROJECT`      | *(empty)*                                   | GCP project for Vertex / Cloud Run ADC          |
| `DATA_JSON_PATH`            | `%LOCALAPPDATA%\BimAgenticBridge\data.json` | Must match plugin                               |
| `DATA_TTL_SECONDS`          | `300`                                       | Stale threshold before re-extract               |

Installed builds prefer DPAPI `credentials.dat` + `config.json` (`api_base_url`, `auth_token`) under `%LOCALAPPDATA%\BimAgenticBridge`.



## Credits

Developed by **[Athis J](https://github.com/codewithathis)**.  
Contact: [trichyathis@gmail.com](mailto:trichyathis@gmail.com) · [LinkedIn](https://www.linkedin.com/in/athis-j) · [Buy me a coffee](https://buymeacoffee.com/codewithathis)
