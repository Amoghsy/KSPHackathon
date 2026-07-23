"""
app/main.py — FastAPI application entry point.

Development:
    uvicorn app.main:app --reload

Production / Zoho Catalyst AppSail:
    python3 -u app_start.py

IMPORTANT:
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

CORS strategy:

    Local development:
        FastAPI CORSMiddleware handles CORS.

    Zoho Catalyst AppSail:
        Catalyst handles CORS.
        FastAPI CORSMiddleware is NOT registered to prevent duplicate
        Access-Control-Allow-Origin headers.
"""

from __future__ import annotations

import asyncio
import logging
import logging.config
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator


# ===========================================================================
# WINDOWS EVENT LOOP COMPATIBILITY
# ===========================================================================

# Psycopg 3 async connections on Windows work correctly with
# WindowsSelectorEventLoopPolicy.
#
# Catalyst AppSail runs Linux, so this does nothing in production.

if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy()
    )


# Import FastAPI after Windows event-loop configuration.

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
        "handlers": ["console"],
    },
}


logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)


# ===========================================================================
# ENVIRONMENT DETECTION
# ===========================================================================

# Catalyst AppSail automatically provides this environment variable.
#
# If it exists, the application is considered to be running behind
# the Catalyst/AppSail gateway.

IS_CATALYST = bool(
    os.getenv("X_ZOHO_CATALYST_LISTEN_PORT")
)


logger.info(
    "Runtime environment detected: %s",
    "Zoho Catalyst AppSail" if IS_CATALYST else "Local / External",
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

    Startup MUST remain lightweight for Catalyst AppSail.

    Do NOT perform the following before yielding:

        - PostgreSQL connection verification
        - Alembic migrations
        - Database table creation
        - Database seeding
        - Redis connection
        - Gemini initialization
        - SMTP initialization
        - External API calls

    Database initialization must be performed separately:

        python -m alembic upgrade head

    Demo data:

        python scripts/seed_db.py

    Dependency health can be checked using:

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

    # Application becomes available immediately.
    yield

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
# CORS CONFIGURATION
# ===========================================================================
#
# IMPORTANT:
#
# LOCAL:
#
#     Browser
#        ↓
#     FastAPI CORSMiddleware
#        ↓
#     API
#
#
# CATALYST:
#
#     Browser
#        ↓
#     Catalyst Gateway / Authentication CORS
#        ↓
#     AppSail
#        ↓
#     FastAPI
#
#
# FastAPI CORSMiddleware MUST NOT also add CORS headers on Catalyst.
#
# Otherwise the response becomes:
#
#     Access-Control-Allow-Origin: frontend-url
#     Access-Control-Allow-Origin: frontend-url
#
# Browsers combine this into:
#
#     frontend-url, frontend-url
#
# which is invalid CORS and causes:
#
#     "The Access-Control-Allow-Origin header contains multiple values"
#
# ===========================================================================


LOCAL_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8080",
]


# Optional additional origins for non-Catalyst environments.
#
# Example:
#
# ALLOWED_ORIGINS=https://example.com,https://staging.example.com

ENV_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


# Remove duplicate origins while preserving order.

ALLOWED_ORIGINS = list(
    dict.fromkeys(
        LOCAL_ORIGINS + ENV_ORIGINS
    )
)


# Optional explicit override.
#
# Normally:
#
# Catalyst:
#     CORS_MANAGED_BY_PLATFORM=true
#
# Local:
#     CORS_MANAGED_BY_PLATFORM=false
#
# If the variable is not configured, Catalyst is detected automatically.

cors_platform_env = os.getenv(
    "CORS_MANAGED_BY_PLATFORM"
)


if cors_platform_env is not None:

    CORS_MANAGED_BY_PLATFORM = (
        cors_platform_env.strip().lower()
        in {"1", "true", "yes", "on"}
    )

else:

    # Automatically use Catalyst CORS when deployed on AppSail.

    CORS_MANAGED_BY_PLATFORM = IS_CATALYST


if CORS_MANAGED_BY_PLATFORM:

    logger.info(
        "FastAPI CORSMiddleware DISABLED. "
        "CORS is managed by the hosting platform."
    )

else:

    logger.info(
        "FastAPI CORSMiddleware ENABLED. "
        "Allowed origins: %s",
        ALLOWED_ORIGINS,
    )

    app.add_middleware(
        CORSMiddleware,

        allow_origins=ALLOWED_ORIGINS,

        allow_credentials=True,

        allow_methods=["*"],

        allow_headers=["*"],
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

    It verifies only:

        Catalyst/AppSail
              ↓
            Python
              ↓
            Uvicorn
              ↓
            FastAPI
    """

    return {
        "status": "ok",

        "service": "scrb-intelligence-backend",

        "app": settings.app_name,

        "environment": settings.app_env,

        "runtime": (
            "catalyst-appsail"
            if IS_CATALYST
            else "local-or-external"
        ),

        "version": "0.1.0",
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
    Verify that critical external dependencies are available.

    Currently verifies:

        PostgreSQL

    HTTP 200:
        Database reachable.

    HTTP 503:
        Database unavailable.

    A readiness failure does NOT necessarily mean FastAPI or AppSail
    itself has failed.
    """

    # Lazy import prevents DB initialization during FastAPI import/startup.

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

        # Log actual exception internally.
        #
        # Never expose raw DB connection details because they may contain:
        #
        # - hostnames
        # - usernames
        # - ports
        # - infrastructure information

        logger.exception(
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
    Return basic application and operational information.
    """

    return {
        "message": (
            f"Welcome to {settings.app_name}"
        ),

        "service": "scrb-intelligence-backend",

        "version": "0.1.0",

        "api_version": "v1",

        "environment": settings.app_env,

        "runtime": (
            "catalyst-appsail"
            if IS_CATALYST
            else "local-or-external"
        ),

        "cors": {
            "managed_by": (
                "platform"
                if CORS_MANAGED_BY_PLATFORM
                else "fastapi"
            ),
        },

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

from app.api.v1.router import api_router  # noqa: E402


app.include_router(
    api_router,
    prefix="/api/v1",
)


# ===========================================================================
# IMPORT-TIME DIAGNOSTICS
# ===========================================================================

logger.info(
    "FastAPI application imported successfully."
)


logger.info(
    "CORS manager: %s",
    (
        "hosting-platform"
        if CORS_MANAGED_BY_PLATFORM
        else "fastapi"
    ),
)


logger.info(
    "Routes registered: %s",
    [
        route.path
        for route in app.routes
    ],
)