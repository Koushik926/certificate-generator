"""Application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.config import settings
from app.db.session import init_db
from app.core.background import shutdown_background


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[return]
    """Startup/shutdown hooks."""
    Path(settings.CERTIFICATE_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    await init_db()
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
    logging.getLogger("certificate-generator").info(
        "Application started — version %s", settings.APP_VERSION
    )
    yield
    await shutdown_background()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check for container orchestration."""
    return {"status": "ok", "version": settings.APP_VERSION}