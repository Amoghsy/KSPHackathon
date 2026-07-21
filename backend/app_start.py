import os

import uvicorn


def get_port() -> int:
    """
    Resolve the HTTP port for the application.

    Zoho Catalyst AppSail provides X_ZOHO_CATALYST_LISTEN_PORT.
    PORT is supported as a generic fallback.
    Local development defaults to 8000.
    """
    raw_port = (
        os.getenv("X_ZOHO_CATALYST_LISTEN_PORT")
        or os.getenv("PORT")
        or "8000"
    )

    try:
        return int(raw_port)
    except (TypeError, ValueError):
        return 8000


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=get_port(),
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )