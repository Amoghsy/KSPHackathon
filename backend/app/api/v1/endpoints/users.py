from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import UserRole
from app.core.security import get_current_user, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserOut

router = APIRouter()


async def check_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to check if current user is an Admin."""
    if current_user.get("role") != UserRole.ADMINISTRATOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. Admin role required.",
        )
    return current_user


@router.get("/", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """List all registered users. Only accessible by Admins."""
    stmt = select(User).order_by(User.id.asc())
    result = await db.execute(stmt)
    users = result.scalars().all()
    return users


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Register a new user. Only accessible by Admins."""
    user_repo = UserRepository(db)
    
    # Check if username already exists
    existing_user = await user_repo.get_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered.",
        )
    
    # Hash password and create User object
    hashed = get_password_hash(user_in.password)
    db_user = User(
        username=user_in.username,
        hashed_password=hashed,
        role=user_in.role,
    )
    
    created = await user_repo.create_user(db_user)
    await db.commit()
    return created


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Delete a user. Only accessible by Admins."""
    # Find the user
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
        
    # Prevent admin from deleting themselves
    if db_user.username == admin_user.get("username"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admins cannot delete their own accounts.",
        )
        
    await db.delete(db_user)
    await db.commit()
    return None
