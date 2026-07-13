import hashlib
import json
import logging
import os
from typing import Any

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class GraphCache:
    """
    Redis cache client for caching built graphs, repeat offender lists,
    detected communities, and graph analytics.
    Uses normalized filter hashes as cache keys with a 15-minute expiration (900s).
    """

    def __init__(self) -> None:
        self._enabled = os.getenv("GRAPH_CACHE_ENABLED", "true").lower() not in (
            "false",
            "0",
            "no",
        )
        self._ttl = 900  # 15 minutes

        if self._enabled:
            logger.info("GraphCache enabled - TTL=%ds", self._ttl)
        else:
            logger.info("GraphCache disabled via GRAPH_CACHE_ENABLED env var.")

    def _make_key(self, category: str, filters: dict[str, Any]) -> str:
        """Create a stable SHA-256 cache key based on sorted filter parameters."""
        sorted_filters = sorted(
            [(k, str(v)) for k, v in filters.items() if v is not None]
        )
        normalized = json.dumps(sorted_filters)
        digest = hashlib.sha256(normalized.encode()).hexdigest()
        return f"gcache:{category}:{digest}"

    async def get(self, category: str, filters: dict[str, Any]) -> dict[str, Any] | None:
        """Retrieve cached graph data or None on miss/error."""
        if not self._enabled:
            return None

        key = self._make_key(category, filters)
        try:
            client = get_redis_client()
            raw = await client.get(key)
            if raw is None:
                logger.debug("GraphCache MISS category=%s key=%s", category, key)
                return None

            logger.info("GraphCache HIT category=%s key=%.16s…", category, key)
            return json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            logger.warning("GraphCache.get error (non-fatal): %s", exc)
            return None

    async def set(
        self, category: str, filters: dict[str, Any], data: dict[str, Any]
    ) -> None:
        """Store graph data in cache with TTL."""
        if not self._enabled:
            return

        key = self._make_key(category, filters)
        try:
            client = get_redis_client()
            await client.set(key, json.dumps(data, default=str), ex=self._ttl)
            logger.debug("GraphCache SET category=%s key=%.16s…", category, key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("GraphCache.set error (non-fatal): %s", exc)
