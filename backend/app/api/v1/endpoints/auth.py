import datetime
import logging
import sqlalchemy as sa
from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    LoginOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    ResendOTPRequest,
    SessionOut
)
from app.models.user import User
from app.models.session import UserSession
from app.core.security import (
    verify_access_token,
    create_access_token,
    blacklist_token,
    oauth2_scheme,
    get_current_user,
    verify_password,
    normalize_role
)
from app.services.auth.otp_service import OTPService
from app.services.session.session_service import SessionService
from app.services.email.email_service import EmailService
from app.services.audit.audit_service import log_security_event
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Extract client IP address in a proxy-aware manner."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        # X-Forwarded-For can contain a chain, return the first one
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post("/login", response_model=LoginOTPResponse | VerifyOTPResponse)
async def login(
    credentials: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1 of two-step login: authenticate password, generate and email OTP code.
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")

    username_or_email = credentials.username.strip()

    # Search for user by username or email
    stmt = select(User).where(
        (sa.func.lower(User.email) == username_or_email.lower()) |
        (User.username == username_or_email)
    )
    res = await db.execute(stmt)
    db_user = res.scalar_one_or_none()

    if not db_user:
        # Audit login failure safely
        await log_security_event(
            db=db,
            event_type="LOGIN_FAILED",
            username=username_or_email,
            ip_address=ip_address,
            user_agent=user_agent,
            reason="INVALID_CREDENTIALS"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Check account status
    if db_user.account_status != "ACTIVE":
        await log_security_event(
            db=db,
            event_type="LOGIN_FAILED",
            user_id=db_user.id,
            username=db_user.username,
            role=normalize_role(db_user.role),
            ip_address=ip_address,
            user_agent=user_agent,
            reason="ACCOUNT_DISABLED"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Verify password
    if not verify_password(credentials.password, db_user.hashed_password):
        await log_security_event(
            db=db,
            event_type="LOGIN_FAILED",
            user_id=db_user.id,
            username=db_user.username,
            role=normalize_role(db_user.role),
            ip_address=ip_address,
            user_agent=user_agent,
            reason="INVALID_CREDENTIALS"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Password matches! Audit password verified
    await log_security_event(
        db=db,
        event_type="LOGIN_PASSWORD_VERIFIED",
        user_id=db_user.id,
        username=db_user.username,
        role=normalize_role(db_user.role),
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Generate OTP Challenge or Bypass
    bypass_usernames = [u.strip() for u in settings.otp_bypass_usernames.split(",") if u.strip()]
    if db_user.username in bypass_usernames:
        # Create server-side session
        session_service = SessionService(db)
        session = await session_service.create_session(
            user_id=db_user.id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Generate JWT with session_id claim
        normalized_role = normalize_role(db_user.role) or db_user.role
        token_payload = {
            "sub": db_user.username,
            "role": normalized_role,
            "id": db_user.id,
            "session_id": session.id
        }
        access_token = create_access_token(token_payload)

        # Optional refresh token
        refresh_payload = {
            "sub": db_user.username,
            "type": "refresh",
            "id": db_user.id,
            "session_id": session.id
        }
        refresh_token = create_access_token(
            refresh_payload, expires_delta=datetime.timedelta(days=7)
        )

        # Audit login success
        await log_security_event(
            db=db,
            event_type="LOGIN_SUCCESS",
            user_id=db_user.id,
            username=db_user.username,
            role=normalized_role,
            ip_address=ip_address,
            user_agent=user_agent,
            summary=f"Successful login (OTP bypassed). Session: {session.id}"
        )

        # Cache user session details in Redis
        try:
            from app.models.district_assignment import UserDistrictAssignment
            stmt_dists = select(UserDistrictAssignment.district).where(
                UserDistrictAssignment.user_id == db_user.id,
                UserDistrictAssignment.is_active == True
            )
            res_dists = await db.execute(stmt_dists)
            assigned_dists = [r[0] for r in res_dists.fetchall()]
            districts_str = ",".join(assigned_dists) if assigned_dists else None

            from app.core.redis import get_redis_client
            import json
            client = get_redis_client()
            user_info = {
                "id": db_user.id,
                "username": db_user.username,
                "role": normalized_role,
                "districts": districts_str,
                "session_id": session.id
            }
            await client.setex(f"session:{db_user.username}", 24 * 3600, json.dumps(user_info))
        except Exception:
            pass

        return {
            "otp_required": False,
            "access_token": access_token,
            "token_type": "bearer",
            "session_id": session.id,
            "username": db_user.username,
            "role": normalized_role,
            "refresh_token": refresh_token,
            "user": {
                "id": str(db_user.id),
                "name": db_user.full_name or db_user.username,
                "username": db_user.username,
                "role": normalized_role,
                "badgeNo": db_user.employee_id or f"KSP-{db_user.id + 10000}",
                "station": "SCRB HQ, Bengaluru"
            }
        }

    otp_service = OTPService()
    otp_data = await otp_service.generate_otp(db_user.id)
    challenge_id = otp_data["challenge_id"]
    otp_code = otp_data["otp_code"]
    expires_in = otp_data["expires_in"]

    # Send OTP Code Email
    email_service = EmailService()
    email_success = await email_service.send_otp_email(db_user.email, db_user.full_name or db_user.username, otp_code)

    if not email_success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send verification code. Please try again.",
        )

    # Audit OTP Sent
    await log_security_event(
        db=db,
        event_type="OTP_SENT",
        user_id=db_user.id,
        username=db_user.username,
        role=normalize_role(db_user.role),
        ip_address=ip_address,
        user_agent=user_agent,
        reason=f"OTP email sent successfully to {db_user.email}"
    )

    return {
        "otp_required": True,
        "challenge_id": challenge_id,
        "expires_in": expires_in,
        "message": "A verification code has been sent to your registered email."
    }


@router.post("/verify-otp", response_model=VerifyOTPResponse)
async def verify_otp(
    payload: VerifyOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 of two-step login: verify OTP challenge, register session, and issue JWT.
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")

    otp_service = OTPService()
    user_id = await otp_service.verify_otp(payload.challenge_id, payload.otp)

    if not user_id:
        await log_security_event(
            db=db,
            event_type="OTP_VERIFICATION_FAILED",
            ip_address=ip_address,
            user_agent=user_agent,
            reason="Invalid OTP code or challenge expired"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification code.",
        )

    # OTP is valid! Retrieve user details
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    db_user = res.scalar_one_or_none()

    if not db_user or db_user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # Create server-side session
    session_service = SessionService(db)
    session = await session_service.create_session(
        user_id=db_user.id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    # Generate JWT with session_id claim
    normalized_role = normalize_role(db_user.role) or db_user.role
    token_payload = {
        "sub": db_user.username,
        "role": normalized_role,
        "id": db_user.id,
        "session_id": session.id
    }
    access_token = create_access_token(token_payload)

    # Optional refresh token
    refresh_payload = {
        "sub": db_user.username,
        "type": "refresh",
        "id": db_user.id,
        "session_id": session.id
    }
    refresh_token = create_access_token(
        refresh_payload, expires_delta=datetime.timedelta(days=7)
    )

    # Audit login success
    await log_security_event(
        db=db,
        event_type="LOGIN_SUCCESS",
        user_id=db_user.id,
        username=db_user.username,
        role=normalized_role,
        ip_address=ip_address,
        user_agent=user_agent,
        summary=f"Successful 2FA login. Session: {session.id}"
    )

    # Cache user session details in Redis for backwards compatibility with legacy routes
    try:
        from app.models.district_assignment import UserDistrictAssignment
        stmt_dists = select(UserDistrictAssignment.district).where(
            UserDistrictAssignment.user_id == db_user.id,
            UserDistrictAssignment.is_active == True
        )
        res_dists = await db.execute(stmt_dists)
        assigned_dists = [r[0] for r in res_dists.fetchall()]
        districts_str = ",".join(assigned_dists) if assigned_dists else None

        from app.core.redis import get_redis_client
        import json
        client = get_redis_client()
        user_info = {
            "id": db_user.id,
            "username": db_user.username,
            "role": normalized_role,
            "districts": districts_str,
            "session_id": session.id
        }
        await client.setex(f"session:{db_user.username}", 24 * 3600, json.dumps(user_info))
    except Exception:
        pass

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "session_id": session.id,
        "username": db_user.username,
        "role": normalized_role,
        "refresh_token": refresh_token,
        "user": {
            "id": str(db_user.id),
            "name": db_user.full_name or db_user.username,
            "username": db_user.username,
            "role": normalized_role,
            "badgeNo": db_user.employee_id or f"KSP-{db_user.id + 10000}",
            "station": "SCRB HQ, Bengaluru"
        }
    }


@router.post("/resend-otp")
async def resend_otp(
    payload: ResendOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Resend verification code for an active OTP challenge, enforcing 60-second cooldown.
    """
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "Unknown")

    otp_service = OTPService()
    try:
        resend_data = await otp_service.resend_otp(payload.challenge_id)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )

    if not resend_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OTP Challenge expired or not found."
        )

    user_id = resend_data["user_id"]
    otp_code = resend_data["otp_code"]
    expires_in = resend_data["expires_in"]

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    db_user = res.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Email OTP code
    email_service = EmailService()
    await email_service.send_otp_email(db_user.email, db_user.full_name or db_user.username, otp_code)

    # Audit resend
    await log_security_event(
        db=db,
        event_type="OTP_SENT",
        user_id=db_user.id,
        username=db_user.username,
        role=normalize_role(db_user.role),
        ip_address=ip_address,
        user_agent=user_agent,
        reason=f"Resent OTP email to {db_user.email}"
    )

    return {
        "status": "success",
        "expires_in": expires_in,
        "message": "A new verification code has been sent."
    }


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Log out of the current device session.
    """
    session_id = current_user.get("session_id")
    token = current_user.get("token")

    if session_id:
        session_service = SessionService(db)
        await session_service.revoke_session(session_id, revoked_by=current_user["id"], reason="LOGOUT")

    if token:
        await blacklist_token(token, expire_seconds=24 * 3600)

    # Invalidate legacy Redis cache session
    try:
        from app.core.redis import get_redis_client
        client = get_redis_client()
        await client.delete(f"session:{current_user['username']}")
    except Exception:
        pass

    # Audit logout
    await log_security_event(
        db=db,
        event_type="LOGOUT",
        user_id=current_user["id"],
        username=current_user["username"],
        role=current_user["role"],
        reason="User requested sign out"
    )

    return {"status": "success", "message": "Successfully logged out."}


@router.get("/sessions", response_model=list[SessionOut])
async def list_active_sessions(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all active devices signed in under the current user.
    """
    session_service = SessionService(db)
    active_sessions = await session_service.get_active_sessions(current_user["id"])

    result = []
    for s in active_sessions:
        is_current = (s.id == current_user["session_id"])
        
        # Derive OS and Browser representation
        os_display = s.operating_system
        browser_display = s.browser

        result.append({
            "session_id": s.id,
            "device_name": s.device_name,
            "browser": browser_display,
            "os": os_display,
            "device_type": s.device_type,
            "ip_address": s.ip_address,
            "created_at": s.created_at.isoformat() + "Z",
            "last_activity_at": s.last_activity_at.isoformat() + "Z",
            "is_current": is_current
        })

    return result


@router.delete("/sessions/{session_id}")
async def revoke_user_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke a specific device session owned by the authenticated user.
    """
    session_service = SessionService(db)
    session = await session_service.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    # Enforce security: users can only revoke their own sessions!
    if session.user_id != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You can only manage your own sessions."
        )

    await session_service.revoke_session(
        session_id=session_id,
        revoked_by=current_user["id"],
        reason="USER_REMOTE_LOGOUT"
    )

    # Blacklist its token identifier in Redis if present
    if session.token_identifier:
        await blacklist_token(session.token_identifier)

    # Audit Remote Logout
    await log_security_event(
        db=db,
        event_type="REMOTE_LOGOUT",
        user_id=current_user["id"],
        username=current_user["username"],
        role=current_user["role"],
        reason=f"User revoked session {session_id} on {session.device_name} (IP: {session.ip_address})"
    )

    return {"status": "success", "message": "Session successfully terminated."}


@router.post("/sessions/logout-others")
async def logout_other_devices(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Revoke all other device sessions except the current active session.
    """
    session_id = current_user.get("session_id")
    session_service = SessionService(db)

    await session_service.revoke_all_user_sessions(
        user_id=current_user["id"],
        except_session_id=session_id,
        revoked_by=current_user["id"],
        reason="USER_REMOTE_LOGOUT_ALL_OTHERS"
    )

    # Audit Session Revoked All
    await log_security_event(
        db=db,
        event_type="SESSION_REVOKED_ALL",
        user_id=current_user["id"],
        username=current_user["username"],
        role=current_user["role"],
        reason="User terminated all other active sessions"
    )

    return {"status": "success", "message": "Successfully terminated all other device sessions."}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for new access and refresh tokens.
    """
    decoded = verify_access_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    username = decoded.get("sub")
    session_id = decoded.get("session_id")

    from app.repositories.user import UserRepository
    user_repo = UserRepository(db)
    db_user = await user_repo.get_by_username(username)
    if not db_user or db_user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account disabled.",
        )

    # Validate corresponding session is still active
    if session_id:
        stmt = select(UserSession).where(UserSession.id == session_id)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()
        if not session or not session.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Corresponding session has been terminated.",
            )

    # Generate new access token
    new_payload = {
        "sub": db_user.username,
        "role": normalize_role(db_user.role),
        "id": db_user.id,
        "session_id": session_id
    }
    new_access = create_access_token(new_payload)

    # Generate new refresh token
    new_refresh = create_access_token(
        {"sub": db_user.username, "type": "refresh", "id": db_user.id, "session_id": session_id},
        expires_delta=datetime.timedelta(days=7)
    )

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "username": db_user.username,
        "role": normalize_role(db_user.role),
        "refresh_token": new_refresh,
    }
