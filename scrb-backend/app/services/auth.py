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

        if db_user:
            if not verify_password(password, db_user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect password",
                )
            
            token_payload = {"sub": db_user.username, "role": db_user.role, "id": db_user.id}
            token = create_access_token(token_payload)
            return {
                "access_token": token,
                "token_type": "bearer",
                "username": db_user.username,
                "role": db_user.role,
            }

        # Admin role must exist in DB
        if role == UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Administrator account not found in database",
            )

        # Fallback to placeholder logic for dev/testing
        token_payload = {"sub": username, "role": role, "id": 999}  # Mock user id
        token = create_access_token(token_payload)
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": username,
            "role": role,
        }
