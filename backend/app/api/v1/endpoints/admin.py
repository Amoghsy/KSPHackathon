import logging
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user, normalize_role
from app.core.rbac import UserRole
from app.models.user import User
from app.models.session import UserSession
from app.services.session.session_service import SessionService
from app.services.audit.audit_service import log_security_event
from app.schemas.auth import SessionOut

logger = logging.getLogger(__name__)
router = APIRouter()


async def check_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to check if current user is an Admin."""
    if current_user.get("role") != UserRole.ADMINISTRATOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Admin role required.",
        )
    return current_user


@router.get("/users/{user_id}/sessions", response_model=list[SessionOut])
async def get_user_sessions_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """
    Retrieve active sessions of a specific user. ADMINISTRATOR ONLY.
    """
    # Verify target user exists
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    db_user = res.scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    session_service = SessionService(db)
    active_sessions = await session_service.get_active_sessions(user_id)

    result = []
    for s in active_sessions:
        result.append({
            "session_id": s.id,
            "device_name": s.device_name,
            "browser": s.browser,
            "os": s.operating_system,
            "device_type": s.device_type,
            "ip_address": s.ip_address,
            "created_at": s.created_at.isoformat() + "Z",
            "last_activity_at": s.last_activity_at.isoformat() + "Z",
            "is_current": False  # Not the admin's current session
        })

    return result


@router.delete("/users/{user_id}/sessions/{session_id}")
async def revoke_user_session_admin(
    user_id: int,
    session_id: str,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """
    Force terminate a specific user session. ADMINISTRATOR ONLY.
    """
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)

    if not session or session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found for this user."
        )

    await session_service.revoke_session(
        session_id=session_id,
        revoked_by=admin_user["id"],
        reason="ADMIN_FORCED_LOGOUT"
    )

    # Invalidate in Redis if token_identifier exists
    if session.token_identifier:
        from app.core.security import blacklist_token
        await blacklist_token(session.token_identifier)

    # Audit Admin forced logout
    await log_security_event(
        db=db,
        event_type="ADMIN_SESSION_REVOKED",
        user_id=admin_user["id"],
        username=admin_user["username"],
        role=admin_user["role"],
        target_user_id=user_id,
        reason=f"Administrator force-logged out session {session_id} on {session.device_name} (IP: {session.ip_address})"
    )

    return {"status": "success", "message": "Session terminated by administrator."}


@router.post("/users/{user_id}/logout-all")
async def logout_all_user_sessions_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """
    Force terminate all device sessions of a specific user. ADMINISTRATOR ONLY.
    """
    # Verify target user exists
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    db_user = res.scalar_one_or_none()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    session_service = SessionService(db)
    await session_service.revoke_all_user_sessions(
        user_id=user_id,
        revoked_by=admin_user["id"],
        reason="ADMIN_FORCED_LOGOUT_ALL"
    )

    # Audit admin revoked all sessions
    await log_security_event(
        db=db,
        event_type="ADMIN_SESSION_REVOKED",
        user_id=admin_user["id"],
        username=admin_user["username"],
        role=admin_user["role"],
        target_user_id=user_id,
        reason="Administrator force-logged out all active sessions of this user."
    )

    return {"status": "success", "message": "All user sessions terminated by administrator."}
