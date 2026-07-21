"""
app/main.py — FastAPI application entry point.

Development:
    uvicorn app.main:app --reload

Production / Zoho Catalyst AppSail:
    python app_start.py
"""

from __future__ import annotations

import asyncio
import logging
import logging.config
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator


# ---------------------------------------------------------------------------
# Windows Event Loop Compatibility
# ---------------------------------------------------------------------------
# Psycopg 3 async connections on Windows work with SelectorEventLoop.
# This block only runs on Windows and has no effect on Linux/AppSail.
# ---------------------------------------------------------------------------

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


# ---------------------------------------------------------------------------
# Structured Logging Configuration
# ---------------------------------------------------------------------------

LOGGING_CONFIG: dict = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "standard": {
            "format": (
                "%(asctime)s | "
                "%(levelname)-8s | "
                "%(name)s | "
                "%(message)s"
            ),
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
        "level": (
            "DEBUG"
            if settings.app_env == "local"
            else "INFO"
        ),
        "handlers": ["console"],
    },
}


logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:
    """
    FastAPI application lifecycle handler.

    Startup:
        - Logs application startup.
        - Attempts to verify the current database connection.
        - Attempts to seed the default administrator.

    Important for Catalyst Phase 1:
        Database initialization failure must NOT prevent FastAPI from
        starting.

        This allows the AppSail deployment itself to be verified using
        /health even before PostgreSQL is migrated to Catalyst Data Store.

    Shutdown:
        - Logs application shutdown.
    """

    logger.info(
        "Starting %s [env=%s]",
        settings.app_name,
        settings.app_env,
    )

    # -----------------------------------------------------------------------
    # Existing PostgreSQL initialization
    #
    # Phase 1 still uses the existing database infrastructure.
    #
    # A DB failure is logged but does not terminate FastAPI so that the
    # AppSail process can still start and respond to /health.
    # -----------------------------------------------------------------------

    try:
        from app.db.init_db import (
            seed_default_admin,
            verify_db_connection,
        )

        await verify_db_connection()

        logger.info(
            "Database connection verified successfully."
        )

        await seed_default_admin()

        logger.info(
            "Default administrator verification completed."
        )

    except Exception as exc:  # noqa: BLE001

        logger.warning(
            "Database initialization/seeding failed at startup. "
            "Application will continue running. Error: %s",
            exc,
        )

    # -----------------------------------------------------------------------
    # Application is now live
    # -----------------------------------------------------------------------

    yield

    # -----------------------------------------------------------------------
    # Shutdown
    # -----------------------------------------------------------------------

    logger.info(
        "Shutting down %s",
        settings.app_name,
    )


# ---------------------------------------------------------------------------
# FastAPI Application
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
# CORS Middleware
# ---------------------------------------------------------------------------
#
# Phase 1:
# Keep the existing local frontend origins.
#
# Later Catalyst frontend deployment phase:
# Move these origins into environment-driven configuration and add the
# production Catalyst frontend URL.
#
# Do NOT change this to allow_origins=['*'] because credentials are enabled.
# ---------------------------------------------------------------------------

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Application Security Middleware
# ---------------------------------------------------------------------------

from app.core.middleware import (  # noqa: E402
    RateLimitingMiddleware,
    SecurityHeadersMiddleware,
)


app.add_middleware(
    SecurityHeadersMiddleware
)

app.add_middleware(
    RateLimitingMiddleware
)


# ===========================================================================
# HEALTH ENDPOINTS
# ===========================================================================


# ---------------------------------------------------------------------------
# Liveness Check
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    tags=["ops"],
    summary="Application liveness check",
)
async def health() -> dict:
    """
    Lightweight application liveness endpoint.

    This endpoint intentionally DOES NOT contact:

    - PostgreSQL
    - Redis
    - Gemini
    - SMTP
    - External APIs
    - Catalyst Data Store
    - Catalyst Cache

    Its only purpose is to verify that:

        Python
            ↓
        Uvicorn
            ↓
        FastAPI

    are running correctly.

    This endpoint is suitable for the initial Zoho Catalyst AppSail
    deployment health/smoke test.
    """

    return {

        "status": "ok",

        "service": "scrb-intelligence-backend",

        "app": settings.app_name,

        "environment": settings.app_env,

        "version": "0.1.0",
    }


# ---------------------------------------------------------------------------
# Readiness Check
# ---------------------------------------------------------------------------

@app.get(
    "/health/ready",
    tags=["ops"],
    summary="Application readiness check",
)
async def readiness() -> dict:
    """
    Application readiness endpoint.

    Unlike /health, this endpoint verifies critical dependencies.

    Phase 1:
        - PostgreSQL

    Future Catalyst phases:
        - Catalyst Data Store
        - Catalyst Cache
        - Other required infrastructure

    Returns:

        HTTP 200
            Application dependency is available.

        HTTP 503
            Required dependency is unavailable.

    A readiness failure does NOT mean the FastAPI/AppSail process itself
    has failed.
    """

    from app.db.init_db import verify_db_connection

    try:

        await verify_db_connection()

        return {

            "status": "ready",

            "service": "scrb-intelligence-backend",

            "app": settings.app_name,

            "environment": settings.app_env,

            "version": "0.1.0",

            "dependencies": {

                "database": {
                    "status": "connected",
                    "provider": "postgresql",
                },

            },
        }

    except Exception as exc:  # noqa: BLE001

        # Log the actual exception internally.
        #
        # Do NOT return raw database connection errors to clients because
        # they may contain hostnames, usernames, ports, or other
        # infrastructure details.

        logger.error(
            "Application readiness check failed: %s",
            exc,
        )

        raise HTTPException(

            status_code=503,

            detail={

                "status": "not_ready",

                "service": "scrb-intelligence-backend",

                "dependencies": {

                    "database": {
                        "status": "unavailable",
                        "provider": "postgresql",
                    },

                },
            },
        )


# ---------------------------------------------------------------------------
# Root Endpoint
# ---------------------------------------------------------------------------

@app.get(
    "/",
    tags=["ops"],
    summary="Application information",
)
async def read_root() -> dict:
    """
    Return basic application information and useful operational endpoints.
    """

    return {

        "message": (
            f"Welcome to {settings.app_name}"
        ),

        "service": "scrb-intelligence-backend",

        "version": "0.1.0",

        "api_version": "v1",

        "environment": settings.app_env,

        "endpoints": {

            "docs": "/docs",

            "redoc": "/redoc",

            "health": "/health",

            "readiness": "/health/ready",

            "api": "/api/v1",
        },
    }


# ===========================================================================
# API V1 ROUTER
# ===========================================================================
#
# Existing application APIs remain registered under:
#
#     /api/v1/*
#
# No existing endpoint behavior is modified by the Catalyst Phase 1 changes.
# ===========================================================================

from app.api.v1.router import api_router  # noqa: E402


app.include_router(
    api_router,
    prefix="/api/v1",
)


# ---------------------------------------------------------------------------
# Startup Diagnostic
# ---------------------------------------------------------------------------

logger.info(
    "Routes registered: %s",
    [route.path for route in app.routes],
)