from fastapi import HTTPException, status

from app.core.rbac import UserRole
from app.core.security import create_access_token


class AuthService:
    async def authenticate_user_placeholder(
        self, username: str, password: str, role: str = "Investigator"
    ) -> dict:
        """
        Mock login validation. Accepts any username/password combination.
        Returns a signed JWT access token.
        """
        # Ensure role is valid
        valid_roles = [r.value for r in UserRole]
        if role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user role. Choose from: {', '.join(valid_roles)}",
            )

        token_payload = {"sub": username, "role": role, "id": 999}  # Mock user id

        token = create_access_token(token_payload)
        return {
            "access_token": token,
            "token_type": "bearer",
            "username": username,
            "role": role,
        }
