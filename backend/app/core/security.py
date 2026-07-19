import datetime
from typing import Any

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.core.rbac import UserRole, normalize_role

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
) -> dict[str, Any]:
    """
    Dependency injection helper to validate the JWT and return user details.
    Queries the database to fetch latest role and district assignments.
    """
    if not token:
        # Fallback dummy user for local development if no token is provided
        return {
            "id": 1,
            "username": "insp_mysuru",
            "role": "INVESTIGATOR",
            "districts": "Mysuru",
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
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject claim",
        )

    from app.db.session import SessionLocal
    from sqlalchemy import select
    from app.models.user import User

    async with SessionLocal() as db_session:
        stmt = select(User).where(User.username == username)
        result = await db_session.execute(stmt)
        db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found in database",
        )

    return {
        "id": db_user.id,
        "username": db_user.username,
        "role": normalize_role(db_user.role),
        "districts": db_user.districts,
    }

