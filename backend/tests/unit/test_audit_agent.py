"""
tests/unit/test_audit_agent.py — Unit tests for Audit Intelligence Agent.
"""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, MagicMock, patch, ANY

import pytest

from app.agents.audit_agent.audit_agent import AuditAgent


@pytest.mark.anyio
class TestAuditAgent:
    @patch("app.agents.audit_agent.audit_agent.get_redis_client")
    async def test_log_action_success_with_null_fields(self, mock_get_redis_client):
        # Mock database session
        db_mock = MagicMock()
        db_mock.commit = AsyncMock()
        db_mock.rollback = AsyncMock()

        # Mock Redis client
        redis_mock = AsyncMock()
        mock_get_redis_client.return_value = redis_mock

        agent = AuditAgent()

        # Call log_action with LOGIN_SUCCESS structure (nullable fields like question/generated_sql/reason/district_id are None)
        await agent.log_action(
            db=db_mock,
            user_id=1,
            username="testuser",
            role="admin",
            api="LOGIN_SUCCESS",
            request_id="req-123",
            status="success",
            question=None,
            generated_sql=None,
            district_id=None,
            reason=None,
        )

        # Assert database insert was called and committed
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()

        # Assert Redis client operations were called for LOGIN_SUCCESS (without failing)
        redis_mock.sadd.assert_called_once()
        redis_mock.incr.assert_called_once()  # audit:investigations count
        redis_mock.hincrby.assert_called_once()  # audit:features counter
        # Ensure no report incr was called since api is "LOGIN_SUCCESS"
        redis_mock.hincrby.assert_any_call(
            ANY, "LOGIN_SUCCESS", 1
        )

    @patch("app.agents.audit_agent.audit_agent.get_redis_client")
    async def test_log_action_district_tracking(self, mock_get_redis_client):
        db_mock = MagicMock()
        db_mock.commit = AsyncMock()
        db_mock.rollback = AsyncMock()
        
        redis_mock = AsyncMock()
        mock_get_redis_client.return_value = redis_mock

        agent = AuditAgent()

        # Test district extraction via district_id
        await agent.log_action(
            db=db_mock,
            user_id=2,
            username="district_user",
            role="officer",
            api="GET_CASES",
            request_id="req-456",
            district_id="Mysuru",
        )
        # Check that Redis hash incr was called for Mysuru
        redis_mock.hincrby.assert_any_call(
            ANY, "Mysuru", 1
        )

        redis_mock.reset_mock()

        # Test district extraction via question
        await agent.log_action(
            db=db_mock,
            user_id=2,
            username="district_user2",
            role="officer",
            api="SEARCH",
            request_id="req-789",
            question="Find active cases in bengaluru",
        )
        redis_mock.hincrby.assert_any_call(
            ANY, "Bengaluru", 1
        )

    @patch("app.agents.audit_agent.audit_agent.get_redis_client")
    async def test_log_action_redis_failure_non_fatal(self, mock_get_redis_client, caplog):
        db_mock = MagicMock()
        db_mock.commit = AsyncMock()
        db_mock.rollback = AsyncMock()

        # Mock Redis client raising an exception on connection
        redis_mock = MagicMock()
        redis_mock.sadd = AsyncMock(side_effect=Exception("Redis connection refused"))
        mock_get_redis_client.return_value = redis_mock

        agent = AuditAgent()

        # Enable log capturing for warning levels
        with caplog.at_level(logging.WARNING):
            # Should not raise exception
            await agent.log_action(
                db=db_mock,
                user_id=1,
                username="testuser",
                role="admin",
                api="LOGIN_SUCCESS",
                request_id="req-123",
                status="success",
            )

        # Assert database insert was called and committed
        db_mock.add.assert_called_once()
        db_mock.commit.assert_called_once()

        # Assert non-fatal warning was logged
        warning_logged = any(
            "Failed to cache audit stats in Redis" in record.message
            for record in caplog.records
        )
        assert warning_logged
