import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import LocalAuthMiddleware
from app.config import bootstrap_settings_from_runtime, get_settings
from app.paths import PRODUCT_NAME
from app.routers import chat

# Credentials + config.json before Settings cache is populated.
bootstrap_settings_from_runtime()

app = FastAPI(
    title=PRODUCT_NAME,
    description=(
        "Customer-facing Gemini or OpenAI agent for Revit BIM room assessment. "
        "Author: Athis J — https://github.com/codewithathis"
    ),
    version=os.environ.get("PRODUCT_VERSION", "1.0.0"),
    contact={
        "name": "Athis J",
        "email": "trichyathis@gmail.com",
        "url": "https://github.com/codewithathis",
    },
)

# Browser CORS only for hosted deployments. Local Revit HttpClient does not need it.
if os.environ.get("VERCEL"):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_middleware(LocalAuthMiddleware)
app.include_router(chat.router)


@app.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "product": PRODUCT_NAME,
        "product_slug": "bim-agentic-bridge",
        "version": settings.product_version or app.version,
    }


@app.get("/about")
def about() -> dict[str, str]:
    settings = get_settings()
    return {
        "product": PRODUCT_NAME,
        "version": settings.product_version or app.version,
        "author": "Athis J",
        "email": "trichyathis@gmail.com",
        "github": "https://github.com/codewithathis",
        "linkedin": "https://www.linkedin.com/in/athis-j",
        # Never include API keys or auth tokens here.
    }
