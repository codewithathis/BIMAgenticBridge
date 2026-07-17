# Backend (FastAPI Agent)

Local OpenAI tool-calling agent that answers chat questions using Revit-exported room JSON.

**Author:** [Athis J](https://github.com/codewithathis) · [trichyathis@gmail.com](mailto:trichyathis@gmail.com)

Credits / about: `GET /about`

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set `OPENAI_API_KEY`. Leave `DATA_JSON_PATH` empty to use the default shared path:

`%LOCALAPPDATA%\BimAgenticBridge\data.json`

## Run

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Endpoint

`POST /chat`

```json
{ "message": "How many doors in room 101?", "data_ready": false, "force_extract": false }
```

Responses:

- `{ "status": "ok", "reply": "..." }`
- `{ "status": "extraction_required", "reason": "..." }` — Revit plugin should export then retry with `data_ready: true`
