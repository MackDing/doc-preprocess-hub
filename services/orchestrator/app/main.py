"""FastAPI app factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from .api import health, jobs
from .config import get_settings

_settings = get_settings()

logging.basicConfig(level=_settings.log_level)


def create_app() -> FastAPI:
    app = FastAPI(
        title="doc-preprocess-hub",
        description="Enterprise document preprocessing API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.include_router(health.router)
    app.include_router(jobs.router)
    return app


app = create_app()
