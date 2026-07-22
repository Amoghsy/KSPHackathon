import datetime
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.core.rbac import UserRole, normalize_role

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

# OAuth2 scheme config
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours in local dev


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hashed version."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def create_access_token(
    data: dict[str, Any], expires_delta: datetime.timedelta | None = None
) -> str:
    """Generate a JWT access token containing the payload data."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is in the Redis blacklist."""
    try:
        from app.core.redis import get_redis_client
        client = get_redis_client()
        res = await client.get(f"blacklist:{token}")
        return res is not None
    except Exception:
        return False


async def blacklist_token(token: str, expire_seconds: int = 3600) -> None:
    """Blacklist a token in Redis with a TTL."""
    try:
        from app.core.redis import get_redis_client
        client = get_redis_client()
        await client.setex(f"blacklist:{token}", expire_seconds, "true")
    except Exception:
        pass


def verify_access_token(token: str) -> dict[str, Any] | None:
    """Validate a JWT token and decode its payload. Returns None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except (jwt.PyJWTError, ValueError):
        return None


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Dependency injection helper to validate the JWT and return user details.
    Queries the database to fetch latest role and district assignments.
    Also validates server-side session active status and inactivity timeout.
    """
    if not token:
        # Fallback dummy user for local development if no token is provided
        return {
            "id": 1,
            "username": "insp_mysuru",
            "role": "INVESTIGATOR",
            "districts": "Mysuru",
            "session_id": "dummy-session-id",
        }

    # Verify if token is blacklisted in Redis
    if await is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or logged out. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str | None = payload.get("sub")
    session_id: str | None = payload.get("session_id")
    if not username or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject or session ID claim",
        )

    from sqlalchemy import select
    from app.models.user import User
    from app.models.session import UserSession
    from app.services.session.session_service import SessionService
    from app.services.audit.audit_service import log_security_event

    # 1. Fetch user
    stmt_user = select(User).where(User.username == username)
    res_user = await db.execute(stmt_user)
    db_user = res_user.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found in database",
        )

    # 2. Check account status
    if db_user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or pending activation",
        )

    # 3. Fetch device session
    stmt_sess = select(UserSession).where(UserSession.id == session_id)
    res_sess = await db.execute(stmt_sess)
    session = res_sess.scalar_one_or_none()

    if not session or not session.is_active or session.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has been revoked or logged out",
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    if session.expires_at < now:
        session.is_active = False
        db.add(session)
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired",
        )

    # 4. Enforce 10-minute inactivity timeout
    last_act = session.last_activity_at
    if (now - last_act).total_seconds() > 10 * 60:
        session.is_active = False
        session.revoked_at = now
        session.revoke_reason = "SESSION_TIMEOUT"
        db.add(session)
        await db.flush()
        
        # Log to audit history
        await log_security_event(
            db=db,
            event_type="SESSION_TIMEOUT",
            user_id=db_user.id,
            username=db_user.username,
            role=normalize_role(db_user.role),
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            reason="Inactivity timeout reached (10 minutes)"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="SESSION_INACTIVE",
        )

    # 5. Throttled activity update (if > 60s since last update)
    session_service = SessionService(db)
    await session_service.update_last_activity(session)

    from app.models.district_assignment import UserDistrictAssignment
    stmt_dists = select(UserDistrictAssignment.district).where(
        UserDistrictAssignment.user_id == db_user.id,
        UserDistrictAssignment.is_active == True
    )
    res_dists = await db.execute(stmt_dists)
    assigned_dists = [r[0] for r in res_dists.fetchall()]
    districts_str = ",".join(assigned_dists) if assigned_dists else None

    return {
        "id": db_user.id,
        "username": db_user.username,
        "role": normalize_role(db_user.role),
        "districts": districts_str,
        "session_id": session_id,
        "token": token,
    }

