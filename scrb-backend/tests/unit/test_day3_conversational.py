"""
tests/unit/test_day3_conversational.py — Unit tests for Day 3 conversational chatbot components.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.exceptions import ConnectionError as RedisConnError
from redis.exceptions import RedisError as RawRedisError

from app.core.redis import RedisCommandError, RedisConnectionError, health_check, ping
from app.services.conversation.context_injector import ContextInjector
from app.services.conversation.entity_memory import EntityMemory
from app.services.conversation.entity_resolver import EntityResolver


# ============================================================================
# Part 2: Redis Integration Tests
# ============================================================================
@pytest.mark.anyio
class TestRedisIntegration:
    @patch("app.core.redis.get_redis_client")
    async def test_ping_success(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_get_client.return_value = mock_client

        result = await ping()
        assert result is True
        mock_client.ping.assert_called_once()

    @patch("app.core.redis.get_redis_client")
    async def test_ping_connection_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(side_effect=RedisConnError("Connection lost"))
        mock_get_client.return_value = mock_client

        with pytest.raises(RedisConnectionError):
            await ping()

    @patch("app.core.redis.get_redis_client")
    async def test_ping_command_error(self, mock_get_client):
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(side_effect=RawRedisError("Syntax error"))
        mock_get_client.return_value = mock_client

        with pytest.raises(RedisCommandError):
            await ping()

    @patch("app.core.redis.ping")
    async def test_health_check_healthy(self, mock_ping):
        mock_ping.return_value = True
        status = await health_check()
        assert status == {"status": "ok", "redis": "connected"}

    @patch("app.core.redis.ping")
    async def test_health_check_unhealthy(self, mock_ping):
        mock_ping.side_effect = RedisConnectionError("Fail")
        status = await health_check()
        assert status["status"] == "error"


# ============================================================================
# Part 4: Entity Resolver Tests
# ============================================================================
class TestEntityResolver:
    def test_resolve_from_question(self):
        resolver = EntityResolver()
        # Accused A102
        e = resolver.resolve("Show accused A102")
        assert e.accused_id == "A102"

        # District and Crime Type
        e = resolver.resolve("Show theft cases in Mysuru")
        assert e.district == "Mysuru"
        assert e.crime_type == "Theft"

        # FIR 123
        e = resolver.resolve("Show FIR 123")
        assert e.case_id == "123"

        # Date Range / Year
        e = resolver.resolve("Show cases in 2025")
        assert e.date_range == "2025"

    def test_resolve_from_rows(self):
        resolver = EntityResolver()
        response = {
            "status": "success",
            "rows": [
                {
                    "crime_no": "FIR-999",
                    "accused_name": "A222",
                    "district": "Bengaluru",
                    "crime_type": "Robbery",
                }
            ],
        }
        # If question does not contain details, extract them from rows
        e = resolver.resolve("Show latest cases", response)
        assert e.case_id == "FIR-999"
        assert e.accused_id == "A222"
        assert e.district == "Bengaluru"
        assert e.crime_type == "Robbery"


# ============================================================================
# Part 5: Context Injection (Follow-up) Tests
# ============================================================================
class TestContextInjector:
    def test_conversation_1(self):
        injector = ContextInjector()
        mem = EntityMemory(last_crime_type="Robbery", last_district="Mysuru")

        # User: Only solved ones
        resolved = injector.inject(
            "Only solved ones", mem, "Show robbery cases in Mysuru"
        )
        assert resolved.lower() == "show solved robbery cases in mysuru"

        # User: Show accused
        # Set last crime type / district
        resolved_accused = injector.inject("Show accused", mem, "Only solved ones")
        assert resolved_accused.lower() == "show accused in robbery cases in mysuru"

    def test_conversation_2(self):
        injector = ContextInjector()
        mem = EntityMemory(last_accused="A102")

        # User: Show his previous cases
        resolved = injector.inject("Show his previous cases", mem, "Show accused A102")
        assert resolved.lower() == "show previous cases of accused a102"

        # User: Only theft
        # Set last accused
        resolved_theft = injector.inject("Only theft", mem, "Show his previous cases")
        assert resolved_theft.lower() == "show theft cases involving accused a102"

    def test_conversation_3(self):
        injector = ContextInjector()
        mem = EntityMemory(last_case="123")

        # User: Who is the accused
        resolved = injector.inject("Who is the accused", mem, "Show FIR 123")
        assert resolved.lower() == "who is the accused in fir 123"

        # User: Where did it happen
        resolved_where = injector.inject(
            "Where did it happen", mem, "Who is the accused"
        )
        assert resolved_where.lower() == "where did fir 123 happen"

    def test_conversation_4(self):
        injector = ContextInjector()
        mem = EntityMemory(last_crime_type="Cyber Crime")

        # User: Only Bengaluru
        resolved_bengaluru = injector.inject(
            "Only Bengaluru", mem, "Show cyber crime cases"
        )
        assert resolved_bengaluru.lower() == "show cyber crime cases in bengaluru"

        # Now update memory with district
        mem.last_district = "Bengaluru"
        # User: Only this month
        resolved_month = injector.inject("Only this month", mem, "Only Bengaluru")
        assert (
            resolved_month.lower()
            == "show cyber crime cases in bengaluru during this month"
        )

    def test_conversation_5(self):
        injector = ContextInjector()
        mem = EntityMemory(last_accused="A210")

        # User: Show his victims
        resolved = injector.inject("Show his victims", mem, "Show accused A210")
        assert resolved.lower() == "show victims of accused a210"

        # User: Show only female victims
        resolved_female = injector.inject(
            "Show only female victims", mem, "Show his victims"
        )
        assert resolved_female.lower() == "show only female victims of accused a210"
