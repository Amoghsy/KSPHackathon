"""
app/services/conversation/session_manager.py — Redis session storage management with structured exceptions.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

import redis.asyncio as aioredis
from redis.exceptions import ConnectionError as RedisConnError
from redis.exceptions import RedisError as RawRedisError
from redis.exceptions import TimeoutError as RedisTimeoutError

from app.core.redis import RedisCommandError, RedisConnectionError, get_redis_client

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages raw session state in Redis.
    Handles serialization/deserialization, TTL setting, and session lifecycle.
    Never exposes raw Redis exceptions; returns structured exceptions instead.
    Falls back to in-memory storage if Redis is down.
    """

    # Class-level in-memory fallback database
    _fallback_db: Dict[str, Dict[str, Any]] = {}

    def __init__(self, client: Any = None, prefix: str = "session:") -> None:
        self._client = client
        self.prefix = prefix
        self.default_expiry = 86400  # 24 hours in seconds

    @property
    def client(self) -> aioredis.Redis:
        """Lazy load or return injected client."""
        if self._client is None:
            self._client = get_redis_client()
        return self._client

    def _key(self, session_id: str) -> str:
        """Construct the Redis key for a given session ID."""
        return f"{self.prefix}{session_id}"

    def _wrap_exception(self, e: Exception) -> Exception:
        """Wrap raw Redis exceptions into structured exceptions."""
        if isinstance(e, (RedisConnError, RedisTimeoutError)):
            return RedisConnectionError(f"Redis connection failed: {e}")
        elif isinstance(e, RawRedisError):
            return RedisCommandError(f"Redis command failed: {e}")
        return e

    async def create_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        expiry: int = 86400,
    ) -> Dict[str, Any]:
        """
        Create a new session in Redis.
        Stores the data as JSON with a specific expiration time (TTL).
        """
        try:
            key = self._key(session_id)
            json_data = json.dumps(data)
            await self.client.set(key, json_data, ex=expiry)
            return data
        except Exception as e:
            logger.warning(
                "Redis error during create_session. Falling back to in-memory: %s", e
            )
            self._fallback_db[session_id] = data
            return data

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session's JSON data from Redis and deserialize it.
        """
        try:
            key = self._key(session_id)
            raw_data = await self.client.get(key)
            if not raw_data:
                return self._fallback_db.get(session_id)
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError:
                logger.error("Failed to decode session JSON data for key: %s", key)
                return None
        except Exception as e:
            logger.warning(
                "Redis error during get_session. Falling back to in-memory: %s", e
            )
            return self._fallback_db.get(session_id)

    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        expiry: int = 86400,
    ) -> Optional[Dict[str, Any]]:
        """
        Update the session data in Redis, overwriting the existing value and resetting the TTL.
        """
        try:
            key = self._key(session_id)
            json_data = json.dumps(data)
            await self.client.set(key, json_data, ex=expiry)
            return data
        except Exception as e:
            logger.warning(
                "Redis error during update_session. Falling back to in-memory: %s", e
            )
            self._fallback_db[session_id] = data
            return data

    async def append_message(
        self,
        session_id: str,
        message: Dict[str, Any],
        expiry: int = 86400,
    ) -> Optional[Dict[str, Any]]:
        """
        Append a message to the session's conversation history.
        Loads the session, updates the conversation_history, and saves the updated session.
        """
        try:
            session_data = await self.get_session(session_id)
            if not session_data:
                session_data = {
                    "conversation_id": session_id,
                    "conversation_history": [],
                    "messages": [],
                    "resolved_entities": {},
                    "created_at": time.time(),
                    "updated_at": time.time(),
                }

            history = session_data.get("conversation_history")
            if not isinstance(history, list):
                history = session_data.get("messages", [])

            history.append(message)
            session_data["conversation_history"] = history
            session_data["messages"] = history
            session_data["updated_at"] = time.time()

            await self.update_session(session_id, session_data, expiry=expiry)
            return session_data
        except Exception as e:
            logger.warning(
                "Redis error during append_message. Falling back to in-memory: %s", e
            )
            session_data = self._fallback_db.get(session_id)
            if not session_data:
                session_data = {
                    "conversation_id": session_id,
                    "conversation_history": [],
                    "messages": [],
                    "resolved_entities": {},
                    "created_at": time.time(),
                    "updated_at": time.time(),
                }
            history = session_data.get("conversation_history", [])
            history.append(message)
            session_data["conversation_history"] = history
            session_data["messages"] = history
            session_data["updated_at"] = time.time()
            self._fallback_db[session_id] = session_data
            return session_data

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete the session key from Redis.
        Returns True if the key was deleted, False otherwise.
        """
        try:
            key = self._key(session_id)
            result = await self.client.delete(key)
            self._fallback_db.pop(session_id, None)
            return bool(result)
        except Exception as e:
            logger.warning(
                "Redis error during delete_session. Falling back to in-memory: %s", e
            )
            existed = session_id in self._fallback_db
            self._fallback_db.pop(session_id, None)
            return existed

    async def expire_session(self, session_id: str, seconds: int) -> bool:
        """
        Update or set the expiration time (TTL) of a session in Redis.
        Returns True if the timeout was set, False otherwise.
        """
        try:
            key = self._key(session_id)
            result = await self.client.expire(key, seconds)
            return bool(result)
        except Exception as e:
            logger.warning(
                "Redis error during expire_session. Falling back to in-memory: %s", e
            )
            return session_id in self._fallback_db
