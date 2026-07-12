"""
app/main.py — FastAPI application entry point.

Start the server:
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import logging
import logging.config
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# ---------------------------------------------------------------------------
# Structured logging configuration
# ---------------------------------------------------------------------------
LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
        },
    },
    "root": {
        "level": "DEBUG" if settings.app_env == "local" else "INFO",
        "handlers": ["console"],
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Runs once at startup (before first request) and once at shutdown.
    Keeps startup logic out of the global module scope.
    """
    logger.info("Starting %s [env=%s]", settings.app_name, settings.app_env)

    try:
        from app.db.init_db import verify_db_connection
        await verify_db_connection()
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB not reachable at startup: %s", exc)

    yield  # ← application is live

    logger.info("Shutting down %s", settings.app_name)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "SCRB Intelligent Conversational AI & Crime Analytics Platform — "
        "backend API for the Karnataka State Police hackathon."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow only the Vite dev server (Day 4 will add production origin)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
@app.get("/health", tags=["ops"])
async def health() -> dict:
    """
    Database connection test health check.
    """
    from fastapi import HTTPException
    from app.db.init_db import verify_db_connection
    try:
        await verify_db_connection()
        return {
            "status": "ok",
            "database": "connected",
            "app": settings.app_name,
            "env": settings.app_env,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {str(exc)}"
        )


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/", tags=["ops"])
def read_root() -> dict:
    """Root endpoint returning basic application information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "health": "/health",
        "version": "v1"
    }


# ---------------------------------------------------------------------------
# API v1 router  (endpoints registered under /api/v1)
# ---------------------------------------------------------------------------
from app.api.v1.router import api_router  # noqa: E402  (import after app creation)

app.include_router(api_router, prefix="/api/v1")


logger.info("Routes registered: %s", [r.path for r in app.routes])
