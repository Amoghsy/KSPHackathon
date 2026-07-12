"""
tests/unit/test_conversation_manager.py — Unit tests for Conversation Manager.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.conversation.context_store import ContextStore, ConversationContext
from app.services.conversation.conversation_manager import ConversationManager
from app.services.conversation.entity_memory import EntityMemory
from app.services.conversation.session_manager import SessionManager


# ============================================================================
# EntityMemory Tests
# ============================================================================
class TestEntityMemory:
    def test_default_initialization(self):
        em = EntityMemory()
        assert em.last_case is None
        assert em.last_accused is None
        assert em.last_victim is None
        assert em.last_station is None
        assert em.last_district is None
        assert em.last_crime_type is None
        assert em.last_date_range is None

    def test_serialization(self):
        em = EntityMemory(
            last_case="Case123",
            last_accused="John Doe",
            last_victim="Jane Smith",
            last_station="Central Station",
            last_district="South District",
            last_crime_type="Theft",
            last_date_range="2026-07-01 to 2026-07-10",
        )
        data = em.to_dict()
        assert data["last_case"] == "Case123"
        assert data["last_accused"] == "John Doe"
        assert data["last_victim"] == "Jane Smith"
        assert data["last_station"] == "Central Station"
        assert data["last_district"] == "South District"
        assert data["last_crime_type"] == "Theft"
        assert data["last_date_range"] == "2026-07-01 to 2026-07-10"

        # Deserialize
        em2 = EntityMemory.from_dict(data)
        assert em2.last_case == "Case123"
        assert em2.last_accused == "John Doe"
        assert em2.last_victim == "Jane Smith"
        assert em2.last_station == "Central Station"
        assert em2.last_district == "South District"
        assert em2.last_crime_type == "Theft"
        assert em2.last_date_range == "2026-07-01 to 2026-07-10"

    def test_update_with_and_without_prefix(self):
        em = EntityMemory()
        # Update with prefixed key
        em.update({"last_case": "CaseABC"})
        assert em.last_case == "CaseABC"

        # Update with non-prefixed key
        em.update({"accused": "Alice"})
        assert em.last_accused == "Alice"

        # Mixed update
        em.update(
            {
                "victim": "Bob",
                "last_station": "Station East",
            }
        )
        assert em.last_victim == "Bob"
        assert em.last_station == "Station East"

        # Verify None values do not overwrite existing values
        em.update(
            {
                "case": None,
                "last_accused": None,
            }
        )
        assert em.last_case == "CaseABC"
        assert em.last_accused == "Alice"


# ============================================================================
# SessionManager Tests
# ============================================================================
@pytest.mark.anyio
class TestSessionManager:
    async def test_create_session(self):
        mock_client = MagicMock()
        mock_client.set = AsyncMock(return_value="OK")
        sm = SessionManager(client=mock_client)

        data = {"hello": "world"}
        result = await sm.create_session("session_123", data, expiry=60)

        assert result == data
        mock_client.set.assert_called_once_with(
            "session:session_123", json.dumps(data), ex=60
        )

    async def test_get_session_success(self):
        mock_client = MagicMock()
        data = {"key": "val"}
        mock_client.get = AsyncMock(return_value=json.dumps(data))
        sm = SessionManager(client=mock_client)

        result = await sm.get_session("session_123")
        assert result == data
        mock_client.get.assert_called_once_with("session:session_123")

    async def test_get_session_not_found(self):
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=None)
        sm = SessionManager(client=mock_client)

        result = await sm.get_session("session_123")
        assert result is None

    async def test_update_session(self):
        mock_client = MagicMock()
        mock_client.set = AsyncMock(return_value="OK")
        sm = SessionManager(client=mock_client)

        data = {"updated": True}
        result = await sm.update_session("session_123", data, expiry=120)

        assert result == data
        mock_client.set.assert_called_once_with(
            "session:session_123", json.dumps(data), ex=120
        )

    async def test_delete_session(self):
        mock_client = MagicMock()
        mock_client.delete = AsyncMock(return_value=1)
        sm = SessionManager(client=mock_client)

        result = await sm.delete_session("session_123")
        assert result is True
        mock_client.delete.assert_called_once_with("session:session_123")

    async def test_expire_session(self):
        mock_client = MagicMock()
        mock_client.expire = AsyncMock(return_value=1)
        sm = SessionManager(client=mock_client)

        result = await sm.expire_session("session_123", 300)
        assert result is True
        mock_client.expire.assert_called_once_with("session:session_123", 300)


# ============================================================================
# ConversationContext and ContextStore Tests
# ============================================================================
@pytest.mark.anyio
class TestContextStore:
    def test_conversation_context_serialization_deserialization(self):
        messages = [{"role": "user", "content": "hello"}]
        context = ConversationContext(
            conversation_id="conv_abc",
            user_id=42,
            messages=messages,
            resolved_entities={
                "last_case": "Case999",
                "last_accused": "Vishwesh",
            },
            last_generated_sql="SELECT * FROM cases;",
        )

        serialized = context.to_dict()
        assert serialized["conversation_id"] == "conv_abc"
        assert serialized["user_id"] == 42
        assert serialized["messages"] == messages
        assert serialized["resolved_entities"]["last_case"] == "Case999"
        assert serialized["resolved_entities"]["last_accused"] == "Vishwesh"
        assert serialized["last_case"] == "Case999"
        assert serialized["last_accused"] == "Vishwesh"
        assert serialized["last_generated_sql"] == "SELECT * FROM cases;"

        # Reload from serialized dict
        reloaded = ConversationContext.from_dict(serialized)
        assert reloaded.conversation_id == "conv_abc"
        assert reloaded.user_id == 42
        assert reloaded.messages == messages
        assert reloaded.entity_memory.last_case == "Case999"
        assert reloaded.entity_memory.last_accused == "Vishwesh"
        assert reloaded.last_generated_sql == "SELECT * FROM cases;"

    async def test_context_store_save_load_delete(self):
        mock_sm = MagicMock(spec=SessionManager)
        mock_sm.update_session = AsyncMock()
        mock_sm.get_session = AsyncMock()
        mock_sm.delete_session = AsyncMock(return_value=True)

        store = ContextStore(session_manager=mock_sm)
        context = ConversationContext(conversation_id="conv_123", user_id=10)

        # Save
        await store.save(context, expiry=100)
        mock_sm.update_session.assert_called_once()
        call_args = mock_sm.update_session.call_args[1]
        assert call_args["session_id"] == "conv_123"
        assert call_args["expiry"] == 100
        assert call_args["data"]["conversation_id"] == "conv_123"

        # Load
        mock_sm.get_session.return_value = context.to_dict()
        loaded = await store.load("conv_123")
        assert loaded is not None
        assert loaded.conversation_id == "conv_123"
        assert loaded.user_id == 10
        mock_sm.get_session.assert_called_once_with("conv_123")

        # Delete
        deleted = await store.delete("conv_123")
        assert deleted is True
        mock_sm.delete_session.assert_called_once_with("conv_123")


# ============================================================================
# ConversationManager Tests
# ============================================================================
@pytest.mark.anyio
class TestConversationManager:
    async def test_conversation_manager_workflow(self):
        mock_store = MagicMock(spec=ContextStore)
        mock_store.save = AsyncMock()
        mock_store.load = AsyncMock()
        mock_store.delete = AsyncMock(return_value=True)

        mgr = ConversationManager(store=mock_store)

        # 1. Create Conversation
        context = await mgr.create_conversation("conv_xyz", user_id=7)
        assert context.conversation_id == "conv_xyz"
        assert context.user_id == 7
        mock_store.save.assert_called_once_with(context, expiry=86400)

        # Reset mocks
        mock_store.save.reset_mock()

        # 2. Get Conversation
        mock_store.load.return_value = context
        loaded = await mgr.get_conversation("conv_xyz")
        assert loaded == context
        mock_store.load.assert_called_once_with("conv_xyz")

        # Reset mocks
        mock_store.load.reset_mock()

        # 3. Update Conversation
        # Test appending a single message, updating entity memory, updating SQL
        await mgr.update_conversation(
            "conv_xyz",
            new_message={"role": "user", "content": "Get accused in Case 5"},
            resolved_entities={"last_case": "Case 5", "last_accused": "Dacoit"},
            last_generated_sql="SELECT * FROM accused WHERE case_no = 5",
        )
        assert len(context.messages) == 1
        assert context.messages[0]["content"] == "Get accused in Case 5"
        assert context.entity_memory.last_case == "Case 5"
        assert context.entity_memory.last_accused == "Dacoit"
        assert context.last_generated_sql == "SELECT * FROM accused WHERE case_no = 5"
        mock_store.save.assert_called_once_with(context, expiry=86400)

        # Reset mocks
        mock_store.save.reset_mock()

        # 4. Save Conversation directly
        await mgr.save_conversation(context, expiry=500)
        mock_store.save.assert_called_once_with(context, expiry=500)

        # 5. Delete Conversation
        deleted = await mgr.delete_conversation("conv_xyz")
        assert deleted is True
        mock_store.delete.assert_called_once_with("conv_xyz")
