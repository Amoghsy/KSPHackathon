"""
tests/unit/test_multilingual.py — Unit tests for multilingual response support.
"""

from __future__ import annotations

import pytest
from app.schemas.chat import ChatRequest
from app.schemas.conversation import ConversationResponse, ConversationUpdate
from app.services.conversation.context_store import ConversationContext
from app.services.llm.prompt_builder import PromptBuilder


def test_chat_request_schema():
    """Verify ChatRequest schema validates response_language."""
    # Test default value
    req = ChatRequest(question="What is the weather?")
    assert req.response_language == "auto"

    # Test custom value
    req2 = ChatRequest(question="What is the weather?", response_language="kn")
    assert req2.response_language == "kn"


def test_conversation_schemas():
    """Verify ConversationResponse and ConversationUpdate schemas."""
    # Test response schema defaults
    resp = ConversationResponse(
        conversation_id="conv-123",
        created_at=12345.6,
        updated_at=12345.6,
        resolved_entities={},
        conversation_history=[],
        preferred_language="en"
    )
    assert resp.preferred_language == "en"

    # Test update schema
    update = ConversationUpdate(preferred_language="kn")
    assert update.preferred_language == "kn"


def test_conversation_context_serialization():
    """Verify ConversationContext correctly serializes preferred_language."""
    context = ConversationContext(
        conversation_id="test-conv",
        preferred_language="kn"
    )
    assert context.preferred_language == "kn"

    # To dict
    data = context.to_dict()
    assert data["preferred_language"] == "kn"

    # From dict
    restored = ConversationContext.from_dict(data)
    assert restored.preferred_language == "kn"


def test_prompt_builder_language_instruction():
    """Verify PromptBuilder compiles correct language instructions."""
    builder = PromptBuilder()

    # Test Kannada
    system, _ = builder.build_summary_prompt("q", "sql", [], 0, response_language="kn")
    assert "Respond only in Kannada. Do not translate after generation. Generate directly in Kannada." in system

    # Test English
    system, _ = builder.build_summary_prompt("q", "sql", [], 0, response_language="en")
    assert "Respond only in English. Do not translate after generation. Generate directly in English." in system

    # Test Auto
    system, _ = builder.build_summary_prompt("q", "sql", [], 0, response_language="auto")
    assert "Respond in the language predominantly used by the user. Do not translate after generation. Generate directly in that language." in system
