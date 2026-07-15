import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from app.services.auth import AuthService
from app.core.security import verify_access_token, create_access_token, blacklist_token, oauth2_scheme

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    User login authentication.
    Validates credentials against database and returns tokens.
    """
    service = AuthService()
    token_details = await service.authenticate_user(
        db=db,
        username=credentials.username,
        password=credentials.password,
        role=credentials.role,
    )
    return token_details


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
    from app.repositories.user import UserRepository
    user_repo = UserRepository(db)
    db_user = await user_repo.get_by_username(username)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in system.",
        )

    # Generate new access token
    new_payload = {"sub": db_user.username, "role": db_user.role, "id": db_user.id}
    new_access = create_access_token(new_payload)

    # Generate new refresh token
    new_refresh = create_access_token(
        {"sub": db_user.username, "type": "refresh", "id": db_user.id},
        expires_delta=datetime.timedelta(days=7)
    )

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "username": db_user.username,
        "role": db_user.role,
        "refresh_token": new_refresh,
    }


@router.post("/logout")
async def logout(
    token: str | None = Depends(oauth2_scheme),
):
    """
    Invalidate current access token.
    """
    if token:
        await blacklist_token(token, expire_seconds=24 * 3600)
    return {"status": "success", "message": "Successfully logged out."}
