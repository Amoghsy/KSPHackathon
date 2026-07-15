import json
import hashlib
import logging
import os
from typing import Any

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


def _is_cache_enabled() -> bool:
    return os.getenv("ANALYTICS_CACHE_ENABLED", "true").lower() not in ("false", "0", "no")


class AnalyticsCache:
    def __init__(self, key_prefix: str = "acache:") -> None:
        self.prefix = key_prefix
        self.ttl = 900  # 15 minutes (15 * 60 = 900 seconds)
        self.enabled = _is_cache_enabled()
        if self.enabled:
            logger.info("AnalyticsCache enabled with prefix=%s and TTL=%ds", self.prefix, self.ttl)
        else:
            logger.info("AnalyticsCache disabled via ANALYTICS_CACHE_ENABLED env var.")

    def _generate_key(self, endpoint: str, filters: dict) -> str:
        """Create a unique cache key based on query filters."""
        # Normalize and sort filters dict
        normalized = {k: str(v).strip().lower() for k, v in filters.items() if v is not None}
        sorted_str = str(sorted(normalized.items()))
        digest = hashlib.sha256(sorted_str.encode()).hexdigest()
        return f"{self.prefix}{endpoint}:{digest}"

    async def get(self, endpoint: str, filters: dict) -> Any | None:
        """Retrieve cached data, returning None on miss or error."""
        if not self.enabled:
            return None

        key = self._generate_key(endpoint, filters)
        try:
            client = get_redis_client()
            raw = await client.get(key)
            if raw:
                logger.info("AnalyticsCache HIT for %s with filters %s", endpoint, filters)
                return json.loads(raw)
            logger.debug("AnalyticsCache MISS for %s", endpoint)
            return None
        except Exception as exc:
            logger.warning("AnalyticsCache.get failed (non-fatal): %s", exc)
            return None

    async def set(self, endpoint: str, filters: dict, data: Any) -> None:
        """Cache data under filter hash with a 15-minute TTL."""
        if not self.enabled:
            return

        key = self._generate_key(endpoint, filters)
        try:
            client = get_redis_client()
            await client.set(key, json.dumps(data, default=str), ex=self.ttl)
            logger.info("AnalyticsCache SET for %s", endpoint)
        except Exception as exc:
            logger.warning("AnalyticsCache.set failed (non-fatal): %s", exc)
