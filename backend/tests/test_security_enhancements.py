import pytest
import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app
from app.db.session import get_db
from app.core.security import get_current_user, create_access_token
from app.models.user import User
from app.models.session import UserSession

client = TestClient(app)


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    return db


@pytest.fixture(autouse=True)
def override_get_db(mock_db):
    app.dependency_overrides[get_db] = lambda: mock_db
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_verify_otp_endpoint_success(mock_db):
    """Test verify-otp endpoint returns credentials and establishes session."""
    user = User(
        id=123,
        username="test_officer",
        email="test_officer@ksp.gov.in",
        role="INVESTIGATOR",
        employee_id="KSP-9999",
        full_name="Test Officer",
        account_status="ACTIVE",
    )
    
    session = UserSession(
        id="sess-12345",
        user_id=123,
        is_active=True,
    )

    with patch("app.services.auth.otp_service.OTPService.verify_otp", return_value=123), \
         patch("app.services.session.session_service.SessionService.create_session", return_value=session):
        
        # Mock database response to get the user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=user)
        mock_db.execute.return_value = mock_result

        # Call verify-otp endpoint
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={"challenge_id": "challenge-xyz", "otp": "123456"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["username"] == "test_officer"
        assert data["role"] == "INVESTIGATOR"
        assert data["session_id"] == "sess-12345"


@pytest.mark.asyncio
async def test_verify_otp_endpoint_invalid_otp():
    """Test verify-otp endpoint rejects invalid code."""
    with patch("app.services.auth.otp_service.OTPService.verify_otp", return_value=None):
        response = client.post(
            "/api/v1/auth/verify-otp",
            json={"challenge_id": "challenge-xyz", "otp": "000000"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid or expired verification code."


@pytest.mark.asyncio
async def test_session_inactivity_timeout_raises_401(mock_db):
    """Test that session inactive for > 10m raises 401 SESSION_INACTIVE."""
    user = User(
        id=123,
        username="test_officer",
        email="test_officer@ksp.gov.in",
        role="INVESTIGATOR",
        employee_id="KSP-9999",
        account_status="ACTIVE",
    )
    
    # Session inactive since 15 minutes ago
    last_activity = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=15)
    session = UserSession(
        id="sess-expired",
        user_id=123,
        is_active=True,
        last_activity_at=last_activity,
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
        ip_address="127.0.0.1",
        user_agent="TestAgent"
    )

    with patch("app.core.security.is_token_blacklisted", return_value=False):
        # First query for user, second for session
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none = MagicMock(return_value=user)
        
        mock_result_sess = MagicMock()
        mock_result_sess.scalar_one_or_none = MagicMock(return_value=session)
        
        # When get_current_user does db.execute, return these
        mock_db.execute.side_effect = [mock_result_user, mock_result_sess]

        # Decode token dependency helper with token mapping to expired session
        token = create_access_token({"sub": "test_officer", "session_id": "sess-expired"})

        # Try to access a protected route with the expired token
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 401
        assert response.json()["detail"] == "SESSION_INACTIVE"


@pytest.mark.asyncio
async def test_revoked_session_raises_401(mock_db):
    """Test that revoked sessions raise 401."""
    user = User(
        id=123,
        username="test_officer",
        email="test_officer@ksp.gov.in",
        role="INVESTIGATOR",
        employee_id="KSP-9999",
        account_status="ACTIVE",
    )
    
    # Revoked session
    session = UserSession(
        id="sess-revoked",
        user_id=123,
        is_active=False, # inactive session
        last_activity_at=datetime.datetime.now(datetime.timezone.utc),
        expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24),
        ip_address="127.0.0.1",
        user_agent="TestAgent",
        revoked_at=datetime.datetime.now(datetime.timezone.utc)
    )

    with patch("app.core.security.is_token_blacklisted", return_value=False):
        mock_result_user = MagicMock()
        mock_result_user.scalar_one_or_none = MagicMock(return_value=user)
        
        mock_result_sess = MagicMock()
        mock_result_sess.scalar_one_or_none = MagicMock(return_value=session)
        
        mock_db.execute.side_effect = [mock_result_user, mock_result_sess]

        token = create_access_token({"sub": "test_officer", "session_id": "sess-revoked"})
        headers = {"Authorization": f"Bearer {token}"}
        
        response = client.get("/api/v1/users/", headers=headers)
        assert response.status_code == 401
        assert "revoked or logged out" in response.json()["detail"]
