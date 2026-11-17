"""Localhost auth token middleware for the installed backend."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

AUTH_HEADER = "X-BimAgentic-Token"
PUBLIC_PATHS = {"/health", "/about", "/docs", "/openapi.json", "/redoc"}


class LocalAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        settings = get_settings()
        path = request.url.path

        if not settings.require_auth or not settings.auth_token:
            return await call_next(request)

        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        provided = request.headers.get(AUTH_HEADER) or request.headers.get(AUTH_HEADER.lower())
        if not provided or provided != settings.auth_token:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "Missing or invalid local auth token. "
                        f"Send header {AUTH_HEADER} matching LocalAppData config.json."
                    )
                },
            )
        return await call_next(request)
