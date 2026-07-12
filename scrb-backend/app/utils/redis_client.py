"""
app/utils/redis_client.py — Redis client initialization.
"""

from __future__ import annotations


from app.core.redis import get_redis_client

# Reusable client delegation
redis_client = get_redis_client()
