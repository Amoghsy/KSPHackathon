"""
app/core/redis.py — Reusable Redis client wrapper with retry logic and structured exceptions.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnError
from redis.exceptions import RedisError as RawRedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


# Structured exceptions
class RedisError(Exception):
    """Base exception for all Redis errors."""

    pass


class RedisConnectionError(RedisError):
    """Raised when there is a connection issue."""

    pass


class RedisCommandError(RedisError):
    """Raised when a command fails to execute."""

    pass


# Global reusable Redis client
_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """
    Get or create the global Redis client using settings.redis_url.
    Configures a connection pool with automatic reconnects, retries, and timeouts.
    """
    global _redis_client
    if _redis_client is None:
        logger.info("Initializing global Redis client connection pool.")
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the global Redis client connection pool."""
    global _redis_client
    if _redis_client is not None:
        try:
            await _redis_client.close()
            logger.info("Redis client closed successfully.")
        except Exception as e:
            logger.error("Error closing Redis client: %s", e)
        finally:
            _redis_client = None


async def ping() -> bool:
    """Ping Redis to test the connection. Never exposes raw Redis exceptions."""
    client = get_redis_client()
    try:
        return await client.ping()
    except (RedisConnError, RedisTimeoutError) as e:
        logger.error("Redis connection error during ping: %s", e)
        raise RedisConnectionError("Failed to connect to Redis.") from e
    except RawRedisError as e:
        logger.error("Redis command error during ping: %s", e)
        raise RedisCommandError("Redis ping command failed.") from e


async def health_check() -> dict[str, Any]:
    """Perform a health check on the Redis connection."""
    try:
        alive = await ping()
        return {"status": "ok", "redis": "connected" if alive else "failed"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    Dependency injection helper to yield a Redis connection.
    Ensures connection errors are caught and converted to RedisConnectionError.
    """
    client = get_redis_client()
    try:
        yield client
    except (RedisConnError, RedisTimeoutError) as e:
        raise RedisConnectionError(
            "Redis connection failed during request context."
        ) from e
    except RawRedisError as e:
        raise RedisCommandError("Redis command failed during request context.") from e
