"""
app/core/middleware.py

Security and rate-limiting middleware implemented as pure ASGI callables.
Using pure ASGI instead of BaseHTTPMiddleware avoids the known streaming/exception
propagation issues that cause hard 500s in FastAPI on Windows uvicorn.
"""
import time
import logging

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware:
    """
    Pure ASGI middleware that injects security response headers.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[b"x-frame-options"] = b"DENY"
                headers[b"x-content-type-options"] = b"nosniff"
                headers[b"x-xss-protection"] = b"1; mode=block"
                headers[b"referrer-policy"] = b"strict-origin-when-cross-origin"
                message = {**message, "headers": list(headers.items())}
            await send(message)

        await self.app(scope, receive, send_with_headers)


class RateLimitingMiddleware:
    """
    Pure ASGI Redis-backed rate limiting middleware.
    Limits to `limit` requests per IP per `window_seconds`.
    """
    EXEMPT_PATHS = {"/docs", "/redoc", "/openapi.json", "/health", "/"}

    def __init__(self, app, limit: int = 150, window_seconds: int = 60):
        self.app = app
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.EXEMPT_PATHS:
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        ip = client[0] if client else "unknown"
        key = f"rate:{ip}"

        try:
            from app.core.redis import get_redis_client
            redis = get_redis_client()
            current = await redis.get(key)

            if current and int(current) >= self.limit:
                body = b"Too many requests. Please try again later."
                response_start = {
                    "type": "http.response.start",
                    "status": 429,
                    "headers": [
                        [b"content-type", b"text/plain"],
                        [b"content-length", str(len(body)).encode()],
                    ],
                }
                response_body = {"type": "http.response.body", "body": body}
                await send(response_start)
                await send(response_body)
                return

            # Fire-and-forget — don't block request on Redis update
            import asyncio
            asyncio.ensure_future(self._increment(redis, key))

        except Exception:
            # Redis unavailable — fail open (allow request)
            pass

        await self.app(scope, receive, send)

    async def _increment(self, redis, key: str):
        try:
            async with redis.pipeline(transaction=True) as pipe:
                await pipe.incr(key)
                await pipe.expire(key, self.window_seconds)
                await pipe.execute()
        except Exception:
            pass
