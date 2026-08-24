from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat

app = FastAPI(
    title="BIM Agentic Bridge",
    description=(
        "Customer-facing Gemini or OpenAI agent for Revit BIM room assessment. "
        "Author: Athis J — https://github.com/codewithathis"
    ),
    version="1.0.0",
    contact={
        "name": "Athis J",
        "email": "trichyathis@gmail.com",
        "url": "https://github.com/codewithathis",
    },
)

# Required for the Revit plugin and any web UI hosted on a different origin (Vercel / Cloud Run).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/about")
def about() -> dict[str, str]:
    return {
        "product": "BIM Agentic Bridge",
        "author": "Athis J",
        "email": "trichyathis@gmail.com",
        "github": "https://github.com/codewithathis",
        "linkedin": "https://www.linkedin.com/in/athis-j",
    }
