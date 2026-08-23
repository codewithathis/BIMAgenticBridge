# Backend (FastAPI Agent)

Gemini / Google ADK or OpenAI tool-calling agent that answers chat questions using Revit-exported room JSON. Deployable to Google Cloud Run.

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

Edit `.env` and set `LLM_PROVIDER` to `gemini` or `openai`. For Gemini, set `GEMINI_API_KEY` (or use GCP Application Default Credentials with `GOOGLE_GENAI_USE_VERTEXAI=true`). For OpenAI, set `OPENAI_API_KEY`. Leave `DATA_JSON_PATH` empty to use the default shared path:

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

## Cloud Run

The `Dockerfile` serves the API on port `8080`. From `backend/`:

```powershell
gcloud run deploy bim-agentic-bridge --source . --region us-central1 --allow-unauthenticated
```

Set `GEMINI_API_KEY` as a secret/env var, or use Vertex AI with the Cloud Run service account (`GOOGLE_GENAI_USE_VERTEXAI=true` and `GOOGLE_CLOUD_PROJECT`). To use OpenAI on Cloud Run instead, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.
