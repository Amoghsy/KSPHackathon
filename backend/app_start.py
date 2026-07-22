"""
app_start.py — Production entry point for Zoho Catalyst AppSail.

This file starts the FastAPI application using Uvicorn.

Zoho Catalyst AppSail provides the HTTP listening port through:

    X_ZOHO_CATALYST_LISTEN_PORT

For local or other deployment environments, PORT is used as a fallback.

If neither environment variable exists, port 8000 is used.
"""

from __future__ import annotations

import os
import sys

import uvicorn


# ===========================================================================
# PORT CONFIGURATION
# ===========================================================================

def get_port() -> int:
    """
    Determine the port that Uvicorn should listen on.

    Priority:

        1. X_ZOHO_CATALYST_LISTEN_PORT
           Provided automatically by Zoho Catalyst AppSail.

        2. PORT
           Generic deployment-platform fallback.

        3. 8000
           Local development fallback.

    Returns:
        int: HTTP listening port.
    """

    raw_port = (
        os.getenv("X_ZOHO_CATALYST_LISTEN_PORT")
        or os.getenv("PORT")
        or "8000"
    )

    try:

        port = int(raw_port)

        # Basic port validation
        if not 1 <= port <= 65535:
            raise ValueError(
                f"Invalid port number: {port}"
            )

        return port

    except (TypeError, ValueError):

        print(
            f"WARNING: Invalid port value '{raw_port}'. "
            "Falling back to port 8000.",
            flush=True,
        )

        return 8000


# ===========================================================================
# APPLICATION STARTUP
# ===========================================================================

if __name__ == "__main__":

    port = get_port()

    # -----------------------------------------------------------------------
    # Startup diagnostics
    #
    # These messages are intentionally printed before Uvicorn starts so
    # they appear directly in Catalyst AppSail logs.
    #
    # Do NOT print environment variable values or secrets here.
    # -----------------------------------------------------------------------

    print(
        "============================================================",
        flush=True,
    )

    print(
        "SCRB Intelligence Platform - Backend Startup",
        flush=True,
    )

    print(
        "============================================================",
        flush=True,
    )

    print(
        f"Python version: {sys.version.split()[0]}",
        flush=True,
    )

    print(
        f"Working directory: {os.getcwd()}",
        flush=True,
    )

    print(
        f"Listening host: 0.0.0.0",
        flush=True,
    )

    print(
        f"Listening port: {port}",
        flush=True,
    )

    print(
        "FastAPI application: app.main:app",
        flush=True,
    )

    print(
        "Starting Uvicorn...",
        flush=True,
    )

    print(
        "============================================================",
        flush=True,
    )

    # -----------------------------------------------------------------------
    # Start Uvicorn
    # -----------------------------------------------------------------------

    try:

        uvicorn.run(

            "app.main:app",

            # AppSail requires the application to listen on all interfaces.
            host="0.0.0.0",

            # Must use the Catalyst-provided listening port.
            port=port,

            # Never enable auto-reload in production.
            reload=False,

            # Trust reverse-proxy headers from Catalyst.
            proxy_headers=True,

            forwarded_allow_ips="*",

            # Standard production log level.
            log_level="info",

            # Log HTTP access requests.
            access_log=True,
        )

    except Exception as exc:

        print(
            "FATAL: Uvicorn failed to start.",
            flush=True,
        )

        print(
            f"Error type: {type(exc).__name__}",
            flush=True,
        )

        print(
            f"Error: {exc}",
            flush=True,
        )

        raise