from fastapi import APIRouter, Depends

from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Mock user login authentication.
    Validates against placeholder logic and returns a signed JWT.
    """
    service = AuthService()
    token_details = await service.authenticate_user_placeholder(
        username=credentials.username,
        password=credentials.password,
        role=credentials.role
    )
    return token_details
