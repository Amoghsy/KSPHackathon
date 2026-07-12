from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    User login authentication.
    Validates against DB if user exists, otherwise falls back to mock logic.
    """
    service = AuthService()
    token_details = await service.authenticate_user(
        db=db,
        username=credentials.username,
        password=credentials.password,
        role=credentials.role,
    )
    return token_details
