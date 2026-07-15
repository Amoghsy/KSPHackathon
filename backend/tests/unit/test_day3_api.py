"""
tests/unit/test_day3_api.py — Unit tests for Day 3 Conversation API endpoints.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api.v1.endpoints.conversations import get_conversation_service
from app.main import app
from app.services.conversation.context_store import ConversationContext
from app.services.conversation.conversation_service import ConversationService


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_service():
    """Mocked ConversationService."""
    service = MagicMock(spec=ConversationService)
    return service


@pytest.fixture(autouse=True)
def override_dependency(mock_service):
    """Autouse fixture to override FastAPI dependency."""
    app.dependency_overrides[get_conversation_service] = lambda: mock_service
    yield
    app.dependency_overrides.clear()


class TestConversationAPI:
    def test_list_conversations(self, mock_service, client):
        context_mock = ConversationContext(
            conversation_id="conv_test_1",
            user_id=1,
            last_question="hello",
            conversation_history=[{"role": "user", "content": "hello"}],
        )
        mock_service.list_conversations = AsyncMock(return_value=[context_mock])

        response = client.get("/api/v1/conversations/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["conversation_id"] == "conv_test_1"
        mock_service.list_conversations.assert_called_once_with(
            limit=20, offset=0, sort_by="updated_at", sort_order="desc"
        )

    def test_get_conversation_found(self, mock_service, client):
        context_mock = ConversationContext(
            conversation_id="conv_test_1",
            user_id=1,
            last_question="hello",
            conversation_history=[{"role": "user", "content": "hello"}],
        )
        mock_service.get_conversation = AsyncMock(return_value=context_mock)

        response = client.get("/api/v1/conversations/conv_test_1")
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv_test_1"

    def test_get_conversation_not_found(self, mock_service, client):
        mock_service.get_conversation = AsyncMock(return_value=None)

        response = client.get("/api/v1/conversations/nonexistent")
        assert response.status_code == 404

    def test_update_conversation(self, mock_service, client):
        context_mock = ConversationContext(
            conversation_id="conv_test_1",
            user_id=1,
            last_question="hello",
            conversation_history=[],
        )
        mock_service.update_conversation_metadata = AsyncMock(return_value=context_mock)

        response = client.patch(
            "/api/v1/conversations/conv_test_1",
            json={"user_id": 2, "last_question": "new question"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == "conv_test_1"
        mock_service.update_conversation_metadata.assert_called_once_with(
            "conv_test_1", {"user_id": 2, "last_question": "new question"}
        )

    def test_delete_conversation(self, mock_service, client):
        mock_service.delete_conversation = AsyncMock(return_value=True)

        response = client.delete("/api/v1/conversations/conv_test_1")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        mock_service.delete_conversation.assert_called_once_with("conv_test_1")
