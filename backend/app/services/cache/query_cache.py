"""
app/services/cache/query_cache.py — Redis-backed SQL query result cache.

Caches the full QueryAgent response (SQL, rows, summary, columns) keyed by a
normalised SHA-256 hash of the user's question.  A cache hit bypasses both LLM
calls AND the database query entirely, dropping repeated-question latency from
2–6 seconds to < 50 ms.

Usage:
    from app.services.cache.query_cache import QueryCache

    cache = QueryCache()
    hit = await cache.get("Show theft cases in Mysuru")
    if hit:
        return hit  # instant response

    # ... run the full pipeline ...

    await cache.set("Show theft cases in Mysuru", response_dict)

Configuration (via environment variables):
    QUERY_CACHE_TTL_SECONDS   Default: 300 (5 minutes)
    QUERY_CACHE_ENABLED       Default: "true"  — set "false" to disable
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

_DEFAULT_TTL = 300  # 5 minutes
_KEY_PREFIX = "qcache:"


def _get_ttl() -> int:
    return int(os.getenv("QUERY_CACHE_TTL_SECONDS", str(_DEFAULT_TTL)))


def _is_enabled() -> bool:
    return os.getenv("QUERY_CACHE_ENABLED", "true").lower() not in ("false", "0", "no")


# ---------------------------------------------------------------------------
# Key generation
# ---------------------------------------------------------------------------


def _normalise(question: str) -> str:
    """Lowercase + collapse whitespace for stable cache keys."""
    return re.sub(r"\s+", " ", question.strip().lower())


def _cache_key(question: str) -> str:
    digest = hashlib.sha256(_normalise(question).encode()).hexdigest()
    return f"{_KEY_PREFIX}{digest}"


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------


class QueryCache:
    """
    Thin async wrapper around Redis for caching QueryAgent responses.

    The cached payload is the full response dict returned by ``format_success``
    (minus transient fields ``request_id`` and ``conversation_id`` which are
    re-injected by the Orchestrator on every request).

    Falls back gracefully on any Redis error — never raises to callers.
    """

    # Fields injected per-request by the Orchestrator; must NOT be cached.
    _EXCLUDE_KEYS: frozenset[str] = frozenset(
        {"request_id", "conversation_id", "agent", "resolved_question"}
    )

    def __init__(self) -> None:
        self._enabled = _is_enabled()
        if self._enabled:
            logger.info(
                "QueryCache enabled — TTL=%ds  prefix=%s",
                _get_ttl(),
                _KEY_PREFIX,
            )
        else:
            logger.info("QueryCache disabled via QUERY_CACHE_ENABLED env var.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get(self, question: str) -> dict[str, Any] | None:
        """
        Return a cached response dict for *question*, or ``None`` on a miss.

        The returned dict is a **copy** — callers may safely mutate it.
        """
        if not self._enabled:
            return None

        key = _cache_key(question)
        try:
            client = get_redis_client()
            raw = await client.get(key)
            if raw is None:
                logger.debug("QueryCache MISS  key=%s", key)
                return None

            payload = json.loads(raw)
            logger.info(
                "QueryCache HIT  key=%.16s…  question=%.80s",
                key[len(_KEY_PREFIX):],
                question,
            )
            return dict(payload)  # return a copy

        except Exception as exc:  # noqa: BLE001
            logger.warning("QueryCache.get error (non-fatal): %s", exc)
            return None

    async def set(self, question: str, response: dict[str, Any]) -> None:
        """
        Store *response* in the cache under the hash of *question*.

        Transient per-request keys (``request_id``, ``conversation_id``, etc.)
        are stripped before storage so cached payloads are reusable.
        """
        if not self._enabled:
            return

        key = _cache_key(question)
        payload = {k: v for k, v in response.items() if k not in self._EXCLUDE_KEYS}

        try:
            client = get_redis_client()
            await client.set(key, json.dumps(payload, default=str), ex=_get_ttl())
            logger.info(
                "QueryCache SET   key=%.16s…  ttl=%ds  question=%.80s",
                key[len(_KEY_PREFIX):],
                _get_ttl(),
                question,
            )

        except Exception as exc:  # noqa: BLE001
            logger.warning("QueryCache.set error (non-fatal): %s", exc)

    async def invalidate(self, question: str) -> bool:
        """
        Explicitly evict the cached entry for *question*.  Returns True if
        a key was deleted.
        """
        if not self._enabled:
            return False

        key = _cache_key(question)
        try:
            client = get_redis_client()
            deleted = await client.delete(key)
            return bool(deleted)
        except Exception as exc:  # noqa: BLE001
            logger.warning("QueryCache.invalidate error (non-fatal): %s", exc)
            return False
