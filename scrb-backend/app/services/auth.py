from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import UserRole
from app.core.security import create_access_token, verify_password
from app.repositories.user import UserRepository


class AuthService:
    async def authenticate_user(
        self, db: AsyncSession, username: str, password: str, role: str = "Investigator"
    ) -> dict:
        """
        Authenticate user. Checks database first. If found, validates password.
        If not found, falls back to mock login validation (for non-admin roles).
        """
        # Ensure role is valid
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user role. Choose from: {', '.join(valid_roles)}",
            )

        # Check DB
        user_repo = UserRepository(db)
        db_user = await user_repo.get_by_username(username)

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in system.",
            )

        if not verify_password(password, db_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )

        import datetime
        import json
        from app.core.redis import get_redis_client

        # Create access token (expires in ACCESS_TOKEN_EXPIRE_MINUTES)
        token_payload = {"sub": db_user.username, "role": db_user.role, "id": db_user.id}
        token = create_access_token(token_payload)

        # Create refresh token (expires in 7 days)
        refresh_payload = {"sub": db_user.username, "type": "refresh", "id": db_user.id}
        refresh_token = create_access_token(
            refresh_payload, expires_delta=datetime.timedelta(days=7)
        )

        # Cache session in Redis
        try:
            client = get_redis_client()
            user_info = {
                "id": db_user.id,
                "username": db_user.username,
                "role": db_user.role,
                "districts": db_user.districts,
            }
            await client.setex(f"session:{db_user.username}", 24 * 3600, json.dumps(user_info))
        except Exception:
            pass

        return {
            "access_token": token,
            "token_type": "bearer",
            "username": db_user.username,
            "role": db_user.role,
            "refresh_token": refresh_token,
        }

