# BimAgenticBridge

AI-based BIM assessment bridge: a Revit 2024 WPF chat plugin that exports room data, plus a local FastAPI agent that answers questions using OpenAI tool-calling against the exported JSON.

## Structure

- `revit-plugin/` — C# .NET Framework 4.8 Revit add-in (dockable chat, room extraction)
- `backend/` — Python FastAPI agent (`POST /chat`)
- Shared export path: `%LOCALAPPDATA%\BimAgenticBridge\data.json`

## Quick start

See full setup steps after the plugin and backend are scaffolded. Summary:

1. Configure `OPENAI_API_KEY` in `backend/.env` (from `.env.example`)
2. Run the API: `cd backend && uvicorn app.main:app --reload --port 8000`
3. Build the Revit plugin, install the `.addin` manifest, open Revit 2024
4. Use the BimAgenticBridge chat panel to ask questions about rooms
