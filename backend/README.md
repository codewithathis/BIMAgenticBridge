# Backend (FastAPI Agent)

Gemini / Google ADK or OpenAI tool-calling agent that answers chat questions using Revit-exported room JSON. Deployable to Vercel (no GCP billing) or Google Cloud Run.

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

## Vercel (recommended if GCP billing is blocked)

`app/main.py` is the FastAPI entrypoint. Deploy with **Root Directory = `backend`**.

```powershell
cd backend
npx vercel login
npx vercel
```

Production:

```powershell
npx vercel --prod
```

In the Vercel project: **Settings → Environment Variables**:

| Name | Example |
|------|---------|
| `LLM_PROVIDER` | `gemini` |
| `GEMINI_API_KEY` | your Gemini API key |
| `GEMINI_MODEL` | `gemini-1.5-flash` |

Do not upload `.env`. After deploy, check `https://YOUR-APP.vercel.app/health` and `POST /chat`.

The deploy includes `backend/data/data.json` (copy of your latest Revit export). On Vercel, `DATA_TTL_SECONDS=0` so that snapshot is not treated as stale. Local Revit still uses `%LOCALAPPDATA%\BimAgenticBridge\data.json` when that file exists. After a new extraction, refresh the snapshot and redeploy:

```powershell
Copy-Item "$env:LOCALAPPDATA\BimAgenticBridge\data.json" .\backend\data\data.json
npx vercel --prod
```

GitHub import: New Project → this repo → **Root Directory** `backend` → add env vars → Deploy.

## Cloud Run

The `Dockerfile` serves the API on port `8080`. Needs a GCP project with billing. From `backend/`:

```powershell
gcloud run deploy bim-agentic-bridge --source . --region us-central1 --allow-unauthenticated
```

Set `GEMINI_API_KEY` as a secret/env var, or use Vertex AI with the Cloud Run service account (`GOOGLE_GENAI_USE_VERTEXAI=true` and `GOOGLE_CLOUD_PROJECT`). To use OpenAI instead, set `LLM_PROVIDER=openai` and `OPENAI_API_KEY`.
