"""
tests/test_query_agent_integration.py — Integration test for the Query Agent.

Mocks the Gemini API response but runs:
1. SQL Generator prompt building
2. SQL Validator schema checks
3. Real Database execution against the seeded Postgres DB
4. Real AuditLog logging and session handling
5. Response Formatter and confidence scoring
"""

import asyncio
import sys

import pytest

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from unittest.mock import MagicMock, patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator.orchestrator import Orchestrator
from app.db.session import SessionLocal
from app.models.audit_log import AuditLog

# Mark as using asyncio
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session


@patch("app.services.llm.gemini_provider.genai.Client")
async def test_query_agent_pipeline_success(mock_genai, db_session: AsyncSession):
    # Mock Gemini provider generate_content response
    mock_client = MagicMock()
    mock_genai.return_value = mock_client

    # 1. Mock SQL generation response
    mock_response_sql = MagicMock()
    mock_candidate_sql = MagicMock()
    mock_candidate_sql.content.parts = [
        MagicMock(text="SELECT name, district FROM police_station LIMIT 5")
    ]
    mock_candidate_sql.finish_reason = "STOP"
    mock_response_sql.candidates = [mock_candidate_sql]
    mock_response_sql.usage_metadata = MagicMock(
        prompt_token_count=100, candidates_token_count=50
    )

    # 2. Mock Summarization response
    mock_response_sum = MagicMock()
    mock_candidate_sum = MagicMock()
    mock_candidate_sum.content.parts = [
        MagicMock(text="Here are the top police stations in the district.")
    ]
    mock_candidate_sum.finish_reason = "STOP"
    mock_response_sum.candidates = [mock_candidate_sum]
    mock_response_sum.usage_metadata = MagicMock(
        prompt_token_count=200, candidates_token_count=30
    )

    # Setup generator and summarizer side effects
    mock_client.models.generate_content.side_effect = [
        mock_response_sql,  # first call: SQL Generator
        mock_response_sum,  # second call: Summarizer
    ]

    # Initialize Orchestrator (it will use the mocked Gemini client)
    with patch.dict("os.environ", {"GEMINI_API_KEY": "dummy-key-for-test"}):
        orch = Orchestrator()

        question = "Show the first 5 police stations."
        import uuid

        request_id = f"test-request-{uuid.uuid4()}"

        # Execute Orchestrator handle
        response = await orch.handle(
            question=question, session=db_session, request_id=request_id, user_id=42
        )

        # Assert response details
        assert response["status"] == "success"
        assert response["question"] == question
        assert "SELECT name, district FROM police_station" in response["generated_sql"]
        assert response["row_count"] > 0
        assert len(response["rows"]) > 0
        assert "name" in response["columns"]
        assert response["request_id"] == request_id
        assert response["agent"] == "query"
        assert response["confidence"] == 1.0
        assert (
            response["summary"] == "Here are the top police stations in the district."
        )

        # Verify audit log was written to DB
        # Run query to find the AuditLog entry
        stmt = select(AuditLog).where(AuditLog.request_id == request_id)
        result = await db_session.execute(stmt)
        log = result.scalars().first()

        assert log is not None
        assert log.question == question
        assert log.generated_sql == response["generated_sql"]
        assert log.request_id == request_id
        assert log.user_id == 42
        assert log.summary == response["summary"]
        assert log.execution_time_ms == pytest.approx(response["execution_time_ms"])


@patch("app.services.llm.gemini_provider.genai.Client")
async def test_query_agent_pipeline_logging_failure_tolerance(
    mock_genai, db_session: AsyncSession
):
    # Mock Gemini provider
    mock_client = MagicMock()
    mock_genai.return_value = mock_client

    mock_response_sql = MagicMock()
    mock_candidate_sql = MagicMock()
    mock_candidate_sql.content.parts = [
        MagicMock(text="SELECT name, district FROM police_station LIMIT 5")
    ]
    mock_candidate_sql.finish_reason = "STOP"
    mock_response_sql.candidates = [mock_candidate_sql]
    mock_response_sql.usage_metadata = MagicMock(
        prompt_token_count=100, candidates_token_count=50
    )

    mock_response_sum = MagicMock()
    mock_candidate_sum = MagicMock()
    mock_candidate_sum.content.parts = [
        MagicMock(text="Here are the top police stations in the district.")
    ]
    mock_candidate_sum.finish_reason = "STOP"
    mock_response_sum.candidates = [mock_candidate_sum]
    mock_response_sum.usage_metadata = MagicMock(
        prompt_token_count=200, candidates_token_count=30
    )

    mock_client.models.generate_content.side_effect = [
        mock_response_sql,
        mock_response_sum,
    ]

    with patch.dict("os.environ", {"GEMINI_API_KEY": "dummy-key-for-test"}):
        orch = Orchestrator()

        # Mock the db_session.add method to raise an exception
        # to simulate database connection loss or constraint violation on audit log table
        with patch.object(
            db_session,
            "add",
            side_effect=Exception("Database connection lost during logging"),
        ):
            question = "Show the first 5 police stations."
            import uuid

            request_id = f"test-request-{uuid.uuid4()}"

            # Execute handle — it should succeed despite the logging exception
            response = await orch.handle(
                question=question, session=db_session, request_id=request_id, user_id=42
            )

            # Assert response details are still correct
            assert response["status"] == "success"
            assert response["question"] == question
            assert (
                "SELECT name, district FROM police_station" in response["generated_sql"]
            )
            assert response["row_count"] > 0
            assert response["request_id"] == request_id
            assert (
                response["summary"]
                == "Here are the top police stations in the district."
            )
