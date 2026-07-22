import secrets
import uuid
import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import UserRole, normalize_role
from app.core.security import get_current_user, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserOut, ActivateAccountPayload
from app.core.redis import get_redis_client
from app.services.email.email_service import EmailService
from app.services.session.session_service import SessionService
from app.services.audit.audit_service import log_security_event

logger = logging.getLogger(__name__)
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
    """Register a new user and trigger activation flow. Only accessible by Admins."""
    user_repo = UserRepository(db)

    # 1. Normalize and validate inputs
    username = user_in.username.strip()
    email = user_in.email.strip().lower()
    employee_id = user_in.employee_id.strip()

    # Check username uniqueness
    existing_username = await user_repo.get_by_username(username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered.",
        )

    # Check email uniqueness (case-insensitive)
    stmt_email = select(User).where(func.lower(User.email) == email)
    res_email = await db.execute(stmt_email)
    if res_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered.",
        )

    # Check employee ID uniqueness
    stmt_emp = select(User).where(User.employee_id == employee_id)
    res_emp = await db.execute(stmt_emp)
    if res_emp.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID already registered.",
        )

    # 2. Setup password strategy
    if user_in.password:
        # If legacy/test code explicitly passes a password, use it and activate account immediately
        hashed = get_password_hash(user_in.password)
        account_status = "ACTIVE"
        must_change_password = False
        activation_token = None
    else:
        # Preferred: Activation link flow
        # Generate random secure dummy hash initially
        hashed = get_password_hash(secrets.token_urlsafe(32))
        account_status = "PENDING_ACTIVATION"
        must_change_password = True
        # Generate cryptographically secure activation token
        activation_token = secrets.token_urlsafe(32)

    db_user = User(
        username=username,
        email=email,
        employee_id=employee_id,
        full_name=user_in.full_name,
        hashed_password=hashed,
        role=normalize_role(user_in.role) or user_in.role,
        account_status=account_status,
        must_change_password=must_change_password,
    )

    created = await user_repo.create_user(db_user)
    await db.flush()

    if user_in.districts:
        from app.models.district_assignment import UserDistrictAssignment
        for d_name in user_in.districts.split(","):
            d_name = d_name.strip()
            if d_name:
                assignment = UserDistrictAssignment(
                    user_id=created.id,
                    district=d_name,
                    is_active=True,
                    assigned_by=admin_user.get("id") if admin_user else None,
                )
                db.add(assignment)
    await db.commit()

    # 3. Store activation token in Redis and send setup email
    if activation_token:
        try:
            redis = get_redis_client()
            # Store token pointing to user ID with 24 hours TTL
            await redis.setex(f"auth:activation:{activation_token}", 86400, str(created.id))
            
            # Send Account Creation / Setup Password Email
            email_service = EmailService()
            await email_service.send_activation_email(
                to_email=created.email,
                name=created.full_name or created.username,
                employee_id=created.employee_id,
                activation_token=activation_token
            )
            
            # Audit account created and activation sent
            await log_security_event(
                db=db,
                event_type="ACCOUNT_CREATED",
                user_id=created.id,
                username=created.username,
                role=created.role,
                target_user_id=created.id,
                reason=f"Account created in PENDING_ACTIVATION state. Activation email sent to {created.email}."
            )
        except Exception as e:
            logger.error(f"Failed to process email activation setup for user {username}: {str(e)}")
            # Do not rollback the user creation since database transaction succeeded,
            # but log warning. Admin can trigger resend.
    else:
        # Audit account created without activation (password pre-supplied)
        await log_security_event(
            db=db,
            event_type="ACCOUNT_CREATED",
            user_id=created.id,
            username=created.username,
            role=created.role,
            target_user_id=created.id,
            reason="Account created in ACTIVE state (password pre-supplied)."
        )

    return created


@router.post("/activate", status_code=status.HTTP_200_OK)
async def activate_account(
    payload: ActivateAccountPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Validate the activation token, set user password, and activate account.
    """
    redis = get_redis_client()
    redis_key = f"auth:activation:{payload.token}"
    user_id_str = await redis.get(redis_key)

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired account activation token."
        )

    user_id = int(user_id_str)
    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    db_user = res.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    # Hash new password and activate
    db_user.hashed_password = get_password_hash(payload.password)
    db_user.account_status = "ACTIVE"
    db_user.must_change_password = False
    
    db.add(db_user)
    await db.commit()

    # Clear activation token
    await redis.delete(redis_key)

    # Audit password changed / account activated
    await log_security_event(
        db=db,
        event_type="PASSWORD_CHANGED",
        user_id=db_user.id,
        username=db_user.username,
        role=db_user.role,
        reason="Account activated and password set by user."
    )

    return {"status": "success", "message": "Account successfully activated. Please log in."}


@router.patch("/{user_id}/status", response_model=UserOut)
async def update_user_status(
    user_id: int,
    status_payload: dict[str, str],
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """
    Update a user's account status (ACTIVE, DISABLED).
    If disabled, terminates all active sessions immediately.
    """
    new_status = status_payload.get("status")
    if new_status not in ["ACTIVE", "DISABLED"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status. Choose ACTIVE or DISABLED."
        )

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    db_user = res.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    db_user.account_status = new_status
    db.add(db_user)

    if new_status == "DISABLED":
        # Revoke all sessions immediately
        session_service = SessionService(db)
        await session_service.revoke_all_user_sessions(
            user_id=db_user.id,
            revoked_by=admin_user["id"],
            reason="ADMIN_ACCOUNT_DISABLE"
        )
        
        # Audit Account Disabled and Sessions Revoked
        await log_security_event(
            db=db,
            event_type="ACCOUNT_DISABLED",
            user_id=admin_user["id"],
            username=admin_user["username"],
            role=admin_user["role"],
            target_user_id=db_user.id,
            reason=f"Account disabled by Admin. Terminated all active sessions."
        )
    else:
        # Audit Account Enabled
        await log_security_event(
            db=db,
            event_type="ACCOUNT_ENABLED",
            user_id=admin_user["id"],
            username=admin_user["username"],
            role=admin_user["role"],
            target_user_id=db_user.id,
            reason="Account re-enabled by Admin."
        )

    await db.commit()
    await db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin_user: dict = Depends(check_admin),
):
    """Delete a user. Only accessible by Admins."""
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

    # Audit deletion
    await log_security_event(
        db=db,
        event_type="ACCOUNT_DELETED",
        user_id=admin_user["id"],
        username=admin_user["username"],
        role=admin_user["role"],
        target_user_id=db_user.id,
        reason=f"Deleted user account '{db_user.username}'."
    )

    await db.delete(db_user)
    await db.commit()
    return None
