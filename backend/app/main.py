"""
app/main.py — FastAPI application entry point.

Development:
    uvicorn app.main:app --reload

Production / Zoho Catalyst AppSail:
    python3 -u app_start.py

Database initialization is intentionally NOT performed during application
startup.

Run migrations and seeding separately:

    python -m alembic upgrade head
    python scripts/seed_db.py

Operational endpoints:

    /health
        Lightweight application liveness check.

    /health/ready
        Readiness check that verifies PostgreSQL connectivity.
"""

from __future__ import annotations

import asyncio
import logging
import logging.config
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator


# ===========================================================================
# WINDOWS EVENT LOOP COMPATIBILITY
# ===========================================================================
#
# Psycopg 3 async connections on Windows work with SelectorEventLoop.
#
# This only affects local Windows development.
# Zoho Catalyst AppSail runs on Linux, so this block has no effect there.
# ===========================================================================

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


# ===========================================================================
# LOGGING
# ===========================================================================

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

        "handlers": [
            "console",
        ],
    },
}


logging.config.dictConfig(
    LOGGING_CONFIG
)


logger = logging.getLogger(
    __name__
)


# ===========================================================================
# APPLICATION LIFESPAN
# ===========================================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:
    """
    FastAPI application lifecycle handler.

    IMPORTANT FOR ZOHO CATALYST APPSAIL:

    Startup must remain lightweight.

    We intentionally DO NOT perform:

        - PostgreSQL connection verification
        - Alembic migrations
        - Database table creation
        - Database seeding
        - Redis connection
        - Gemini initialization
        - SMTP initialization
        - External API calls

    before yielding control to FastAPI.

    This ensures AppSail can start the application immediately and
    successfully perform its liveness checks.

    Database initialization is handled separately:

        python -m alembic upgrade head

    Demo/initial data is seeded separately:

        python scripts/seed_db.py

    PostgreSQL availability can be checked through:

        GET /health/ready
    """

    logger.info(
        "Starting %s [env=%s]",
        settings.app_name,
        settings.app_env,
    )

    logger.info(
        "FastAPI startup initialized. "
        "External dependency checks are not blocking startup."
    )

    # -----------------------------------------------------------------------
    # IMPORTANT:
    #
    # Application becomes live here.
    #
    # Nothing that depends on PostgreSQL, Redis, Gemini, SMTP, etc.
    # should run before this yield.
    # -----------------------------------------------------------------------

    yield

    # -----------------------------------------------------------------------
    # Shutdown
    # -----------------------------------------------------------------------

    logger.info(
        "Shutting down %s",
        settings.app_name,
    )


# ===========================================================================
# FASTAPI APPLICATION
# ===========================================================================

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


# ===========================================================================
# CORS MIDDLEWARE
# ===========================================================================
#
# Current local frontend origins are preserved.
#
# When the frontend is deployed, add the production frontend origin here
# or move this configuration to an environment variable.
#
# Do NOT use:
#
#     allow_origins=["*"]
#
# while:
#
#     allow_credentials=True
#
# ===========================================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8080",
    ],

    allow_credentials=True,

    allow_methods=[
        "*",
    ],

    allow_headers=[
        "*",
    ],
)


# ===========================================================================
# APPLICATION SECURITY MIDDLEWARE
# ===========================================================================

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
# HEALTH ENDPOINT
# ===========================================================================

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
        - Catalyst services

    It only verifies:

        AppSail
            ↓
        Python
            ↓
        Uvicorn
            ↓
        FastAPI

    are running successfully.

    This endpoint should remain lightweight.
    """

    return {

        "status": "ok",

        "service": (
            "scrb-intelligence-backend"
        ),

        "app": (
            settings.app_name
        ),

        "environment": (
            settings.app_env
        ),

        "version": (
            "0.1.0"
        ),
    }


# ===========================================================================
# READINESS ENDPOINT
# ===========================================================================

@app.get(
    "/health/ready",
    tags=["ops"],
    summary="Application readiness check",
)
async def readiness() -> dict:
    """
    Application readiness endpoint.

    Unlike /health, this endpoint checks critical external dependencies.

    Current dependency:

        PostgreSQL

    Expected responses:

        HTTP 200
            PostgreSQL is reachable.

        HTTP 503
            PostgreSQL is unavailable.

    A readiness failure does NOT mean that FastAPI or AppSail itself
    has failed.
    """

    # Import lazily so database modules are not required during
    # application startup.
    from app.db.init_db import (
        verify_db_connection,
    )

    try:

        await verify_db_connection()

        return {

            "status": (
                "ready"
            ),

            "service": (
                "scrb-intelligence-backend"
            ),

            "app": (
                settings.app_name
            ),

            "environment": (
                settings.app_env
            ),

            "version": (
                "0.1.0"
            ),

            "dependencies": {

                "database": {

                    "status": (
                        "connected"
                    ),

                    "provider": (
                        "postgresql"
                    ),
                },
            },
        }

    except Exception as exc:  # noqa: BLE001

        # Log the real exception internally.
        #
        # Do not expose raw database errors to clients because they may
        # contain hostnames, ports, usernames, or infrastructure details.

        logger.exception(
            "Application readiness check failed: %s",
            exc,
        )

        raise HTTPException(

            status_code=503,

            detail={

                "status": (
                    "not_ready"
                ),

                "service": (
                    "scrb-intelligence-backend"
                ),

                "dependencies": {

                    "database": {

                        "status": (
                            "unavailable"
                        ),

                        "provider": (
                            "postgresql"
                        ),
                    },
                },
            },
        ) from exc


# ===========================================================================
# ROOT ENDPOINT
# ===========================================================================

@app.get(
    "/",
    tags=["ops"],
    summary="Application information",
)
async def read_root() -> dict:
    """
    Return basic application information and operational endpoint paths.
    """

    return {

        "message": (
            f"Welcome to {settings.app_name}"
        ),

        "service": (
            "scrb-intelligence-backend"
        ),

        "version": (
            "0.1.0"
        ),

        "api_version": (
            "v1"
        ),

        "environment": (
            settings.app_env
        ),

        "endpoints": {

            "docs": (
                "/docs"
            ),

            "redoc": (
                "/redoc"
            ),

            "health": (
                "/health"
            ),

            "readiness": (
                "/health/ready"
            ),

            "api": (
                "/api/v1"
            ),
        },
    }


# ===========================================================================
# API V1 ROUTER
# ===========================================================================
#
# Existing application APIs remain available under:
#
#     /api/v1/*
#
# Examples:
#
#     /api/v1/auth/login
#     /api/v1/cases/
#     /api/v1/dashboard/
#     /api/v1/chat/
#     /api/v1/network/
#
# ===========================================================================

from app.api.v1.router import api_router  # noqa: E402


app.include_router(

    api_router,

    prefix="/api/v1",
)


# ===========================================================================
# IMPORT-TIME DIAGNOSTIC
# ===========================================================================

logger.info(
    "FastAPI application imported successfully."
)


logger.info(
    "Routes registered: %s",
    [
        route.path
        for route in app.routes
    ],
)