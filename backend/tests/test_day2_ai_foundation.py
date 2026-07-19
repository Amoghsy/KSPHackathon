"""
tests/test_day2_ai_foundation.py — Unit + integration tests for Day 2.

Covers:
    Part 4 — LLM Provider, Factory, Prompt Builder, Schema Context, Examples, SQL Generator
    Part 5 — Query Agent, Response Formatter, Exceptions
    Part 6 — Orchestrator, Agent Registry, Chat Schemas
"""

from __future__ import annotations

import asyncio
import re
from unittest.mock import MagicMock, patch

import pytest

# ========================================================================
# Part 4: LLM Provider Layer
# ========================================================================


class TestBaseLLMProvider:
    def test_response_dataclass(self):
        from app.services.llm.base import LLMResponse

        r = LLMResponse(content="hello", model="test", input_tokens=10, output_tokens=5)
        assert r.content == "hello"
        assert r.model == "test"
        assert r.input_tokens == 10
        assert r.output_tokens == 5

    def test_error_dataclass(self):
        from app.services.llm.base import LLMError

        e = LLMError(error="fail", error_type="test", retryable=True)
        assert e.error == "fail"
        assert e.retryable is True

    def test_cannot_instantiate_abstract(self):
        from app.services.llm.base import BaseLLMProvider

        with pytest.raises(TypeError):
            BaseLLMProvider()


class TestLLMFactory:
    def test_gemini_registered(self):
        from app.services.llm.llm_factory import LLMFactory

        assert "gemini" in LLMFactory.available_providers()

    def test_unknown_provider_raises(self):
        from app.services.llm.llm_factory import LLMFactory

        with pytest.raises(ValueError, match="Unknown LLM provider"):
            LLMFactory.create("nonexistent")

    def test_register_custom_provider(self):
        from app.services.llm.base import BaseLLMProvider
        from app.services.llm.llm_factory import LLMFactory, register_provider

        class DummyProvider(BaseLLMProvider):
            async def generate(self, prompt, **kw):
                pass

            async def chat(self, messages, **kw):
                pass

            async def health_check(self):
                return True

        register_provider("dummy_test", DummyProvider)
        assert "dummy_test" in LLMFactory.available_providers()


class TestPromptBuilder:
    def test_nl2sql_prompt_structure(self):
        from app.services.llm.prompt_builder import PromptBuilder

        pb = PromptBuilder(schema_context="TABLE: test_table", examples="Example 1:")
        sys_p, usr_p = pb.build_nl2sql_prompt("How many cases?")

        assert "PostgreSQL" in sys_p
        assert "test_table" in sys_p
        assert "Example 1:" in sys_p
        assert "CANNOT_GENERATE_SQL" in sys_p
        assert "How many cases?" in usr_p

    def test_summary_prompt_structure(self):
        from app.services.llm.prompt_builder import PromptBuilder

        pb = PromptBuilder()
        sys_p, usr_p = pb.build_summary_prompt(
            question="test?",
            sql="SELECT 1",
            rows=[{"a": 1}],
            row_count=1,
        )
        assert (
            "data analyst" in sys_p.lower()
            or "summarise" in sys_p.lower()
            or "Summarise" in sys_p
        )
        assert "test?" in usr_p
        assert "SELECT 1" in usr_p

    def test_summary_prompt_empty_rows(self):
        from app.services.llm.prompt_builder import PromptBuilder

        pb = PromptBuilder()
        _, usr_p = pb.build_summary_prompt(
            question="test?",
            sql="SELECT 1",
            rows=[],
            row_count=0,
        )
        assert "empty" in usr_p.lower()


# ========================================================================
# Part 4: NL2SQL Layer
# ========================================================================


class TestSchemaContext:
    def test_schema_contains_all_tables(self):
        from app.services.nl2sql.schema_context import get_schema_context

        schema = get_schema_context()
        for table in [
            "case_master",
            "police_station",
            "crime_type",
            "accused_master",
            "victim_master",
            "financial_transaction",
            "users",
        ]:
            assert table in schema, f"Missing table: {table}"

    def test_schema_contains_columns(self):
        from app.services.nl2sql.schema_context import get_schema_context

        schema = get_schema_context()
        assert "crime_no" in schema
        assert "case_master_id" in schema
        assert "police_station_id" in schema

    def test_schema_dict_structure(self):
        from app.services.nl2sql.schema_context import get_schema_dict

        tables = get_schema_dict()
        assert len(tables) >= 7
        for t in tables:
            assert "table" in t
            assert "columns" in t
            assert "primary_keys" in t
            assert "foreign_keys" in t


class TestFewShotExamples:
    def test_example_count(self):
        from app.services.nl2sql.examples import FEW_SHOT_EXAMPLES

        assert len(FEW_SHOT_EXAMPLES) == 17

    def test_examples_have_question_and_sql(self):
        from app.services.nl2sql.examples import FEW_SHOT_EXAMPLES

        for ex in FEW_SHOT_EXAMPLES:
            assert ex.question, f"Empty question: {ex}"
            assert ex.sql, f"Empty SQL: {ex}"
            assert (
                ex.sql.strip().upper().startswith("SELECT")
            ), f"SQL should start with SELECT: {ex.sql[:50]}"

    def test_format_examples(self):
        from app.services.nl2sql.examples import format_examples_for_prompt

        text = format_examples_for_prompt()
        assert "Example 1:" in text
        assert "Example 15:" in text

    def test_no_write_operations_in_examples(self):
        from app.services.nl2sql.examples import FEW_SHOT_EXAMPLES

        blocked = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE"}
        for ex in FEW_SHOT_EXAMPLES:
            tokens = set(re.findall(r"\b[A-Z]+\b", ex.sql.upper()))
            violations = tokens & blocked
            assert not violations, f"Example contains blocked keywords: {violations}"


class TestSQLGenerator:
    def test_clean_sql_strips_fences(self):
        from app.services.nl2sql.sql_generator import SQLGenerator

        assert SQLGenerator._clean_sql("```sql\nSELECT 1\n```") == "SELECT 1"
        assert SQLGenerator._clean_sql("```\nSELECT 1\n```") == "SELECT 1"
        assert SQLGenerator._clean_sql("`SELECT 1`") == "SELECT 1"

    def test_clean_sql_strips_semicolons(self):
        from app.services.nl2sql.sql_generator import SQLGenerator

        assert SQLGenerator._clean_sql("SELECT 1;") == "SELECT 1"

    def test_clean_sql_preserves_content(self):
        from app.services.nl2sql.sql_generator import SQLGenerator

        sql = "SELECT cm.crime_no FROM case_master cm LIMIT 100"
        assert SQLGenerator._clean_sql(sql) == sql

    def test_empty_question_raises(self):
        """SQLGenerator.generate() should reject empty questions (even without API key)."""
        # We can't instantiate SQLGenerator without GEMINI_API_KEY,
        # so we test the validation indirectly.
        from app.services.nl2sql.sql_generator import SQLGenerator

        # Patch the factory to avoid API key requirement.
        with patch("app.services.nl2sql.sql_generator.LLMFactory") as mock_factory:
            mock_provider = MagicMock()
            mock_factory.create.return_value = mock_provider
            gen = SQLGenerator()
            with pytest.raises(ValueError, match="empty"):
                asyncio.get_event_loop().run_until_complete(gen.generate(""))


# ========================================================================
# Part 5: Query Agent
# ========================================================================


class TestExceptions:
    def test_base_exception(self):
        from app.agents.query_agent.exceptions import QueryAgentError

        e = QueryAgentError("test", "test_type", retryable=True)
        assert str(e) == "test"
        assert e.error_type == "test_type"
        assert e.retryable is True

    def test_specific_exceptions(self):
        from app.agents.query_agent.exceptions import (
            DatabaseUnavailableError,
            LLMUnavailableError,
            SQLExecutionError,
            SQLGenerationError,
            SQLValidationError,
            SummaryError,
        )

        assert SQLGenerationError().error_type == "sql_generation_failed"
        assert SQLValidationError("bad sql").error_type == "sql_validation_failed"
        assert SQLExecutionError().error_type == "sql_execution_failed"
        assert SummaryError().error_type == "summary_failed"
        assert DatabaseUnavailableError().retryable is True
        assert LLMUnavailableError().retryable is True


class TestResponseFormatter:
    def test_format_success(self):
        from app.agents.query_agent.response_formatter import format_success

        resp = format_success(
            question="test?",
            generated_sql="SELECT 1",
            rows=[{"a": 1}],
            columns=["a"],
            row_count=1,
            execution_time_ms=5.0,
            summary="One row.",
            confidence=0.95,
        )
        assert resp["status"] == "success"
        assert resp["question"] == "test?"
        assert resp["row_count"] == 1
        assert resp["confidence"] == 0.95

    def test_format_error(self):
        from app.agents.query_agent.response_formatter import format_error

        resp = format_error(
            question="test?",
            error="Failed",
            error_type="sql_generation_failed",
            retryable=True,
        )
        assert resp["status"] == "error"
        assert resp["retryable"] is True

    def test_compute_confidence_perfect(self):
        from app.agents.query_agent.response_formatter import compute_confidence

        c = compute_confidence(
            sql_valid=True,
            rows_returned=10,
            execution_ok=True,
            summary_ok=True,
        )
        assert c == 1.0

    def test_compute_confidence_no_rows(self):
        from app.agents.query_agent.response_formatter import compute_confidence

        c = compute_confidence(
            sql_valid=True,
            rows_returned=0,
            execution_ok=True,
            summary_ok=True,
        )
        assert c == 0.7  # 0.30 + 0.30 + 0.10

    def test_compute_confidence_nothing(self):
        from app.agents.query_agent.response_formatter import compute_confidence

        c = compute_confidence(
            sql_valid=False,
            rows_returned=0,
            execution_ok=False,
            summary_ok=False,
        )
        assert c == 0.0


# ========================================================================
# Part 6: Orchestrator + Agent Registry
# ========================================================================


class TestAgentRegistry:
    def test_register_and_get(self):
        from app.agents.orchestrator.router import AgentRegistry

        reg = AgentRegistry()
        reg.register("test", lambda: "agent_instance")
        assert reg.has("test")
        assert reg.get("test") == "agent_instance"

    def test_unknown_agent_raises(self):
        from app.agents.orchestrator.router import AgentRegistry

        reg = AgentRegistry()
        with pytest.raises(KeyError, match="Unknown agent"):
            reg.get("nonexistent")

    def test_available_agents(self):
        from app.agents.orchestrator.router import AgentRegistry

        reg = AgentRegistry()
        reg.register("b_agent", lambda: None)
        reg.register("a_agent", lambda: None)
        assert reg.available_agents() == ["a_agent", "b_agent"]

    def test_case_insensitive(self):
        from app.agents.orchestrator.router import AgentRegistry

        reg = AgentRegistry()
        reg.register("Query", lambda: "q")
        assert reg.has("query")
        assert reg.get("QUERY") == "q"


class TestChatSchemas:
    def test_request_validation(self):
        from app.schemas.chat import ChatRequest

        req = ChatRequest(question="How many cases?")
        assert req.question == "How many cases?"

    def test_request_empty_question_rejected(self):
        from pydantic import ValidationError

        from app.schemas.chat import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(question="")

    def test_request_too_long_rejected(self):
        from pydantic import ValidationError

        from app.schemas.chat import ChatRequest

        with pytest.raises(ValidationError):
            ChatRequest(question="x" * 2001)

    def test_response_model(self):
        from app.schemas.chat import ChatResponse

        resp = ChatResponse(
            request_id="abc",
            question="test",
            generated_sql="SELECT 1",
            row_count=0,
            execution_time_ms=1.0,
            summary="none",
            confidence=0.5,
        )
        assert resp.status == "success"
        assert resp.request_id == "abc"

    def test_error_response_model(self):
        from app.schemas.chat import ChatErrorResponse

        resp = ChatErrorResponse(
            request_id="abc",
            error="fail",
            error_type="test",
        )
        assert resp.status == "error"
        assert resp.retryable is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
