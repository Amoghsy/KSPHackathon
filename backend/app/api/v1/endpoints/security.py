import datetime
import uuid
from typing import Any
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission, get_user_authorized_districts
from app.core.rbac import Permission, normalize_role
from app.models.district_assignment import UserDistrictAssignment
from app.models.access_request import DistrictAccessRequest, TemporaryDistrictPermission
from app.models.user import User
from app.agents.audit_agent.audit_agent import AuditAgent

router = APIRouter()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class AccessRequestCreate(BaseModel):
    requested_district: str
    related_case_id: int | None = None
    reason: str
    duration_hours: int


class AccessRequestReview(BaseModel):
    review_comment: str


class DistrictAssignmentCreate(BaseModel):
    user_id: int
    district: str


class ReassignBody(BaseModel):
    new_district: str


# Helper to assert supervisor district scope
async def verify_supervisor_scope(supervisor: dict, district: str, db: AsyncSession) -> None:
    role = normalize_role(supervisor.get("role"))
    if role == "SUPERVISOR":
        supervisor_districts = await get_user_authorized_districts(supervisor, db)
        if "__ALL__" not in supervisor_districts and district not in supervisor_districts:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Supervisor is not authorized to manage actions for district '{district}' outside of their supervision scope."
            )


# ---------------------------------------------------------------------------
# 1. Temporary District Access Requests
# ---------------------------------------------------------------------------

@router.post("/access-requests")
async def create_access_request(
    body: AccessRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit a temporary access request for a district."""
    # Ensure they have search permission (investigators/analysts)
    check_perm = require_permission(Permission.SEARCH_CASES)
    await check_perm(current_user)

    request = DistrictAccessRequest(
        requester_id=current_user.get("id"),
        requested_district=body.requested_district,
        related_case_id=body.related_case_id,
        reason=body.reason,
        duration_hours=body.duration_hours,
        status="PENDING",
        requested_at=datetime.datetime.utcnow()
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)

    # Audit log entry
    audit = AuditAgent()
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api="/api/v1/security/access-requests",
        request_id=f"req-{uuid.uuid4()}",
        action="CREATE_ACCESS_REQUEST",
        district_id=body.requested_district,
        case_id=body.related_case_id,
        reason=body.reason,
        summary=f"Created temporary access request for district '{body.requested_district}' (duration: {body.duration_hours}h)"
    )

    return request


@router.get("/access-requests/my")
async def get_my_requests(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve all access requests submitted by the logged in investigator."""
    check_perm = require_permission(Permission.SEARCH_CASES)
    await check_perm(current_user)

    stmt = select(DistrictAccessRequest).where(
        DistrictAccessRequest.requester_id == current_user.get("id")
    ).order_by(DistrictAccessRequest.requested_at.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/access-requests/pending")
async def get_pending_requests(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve pending access requests within a supervisor's scope."""
    check_perm = require_permission(Permission.APPROVE_ACCESS_REQUESTS)
    await check_perm(current_user)

    role = normalize_role(current_user.get("role"))
    supervisor_districts = await get_user_authorized_districts(current_user, db)

    stmt = select(DistrictAccessRequest).where(
        DistrictAccessRequest.status == "PENDING"
    ).order_by(DistrictAccessRequest.requested_at.asc())

    result = await db.execute(stmt)
    requests = result.scalars().all()

    # Filter to supervisor scope if role is SUPERVISOR
    if role == "SUPERVISOR" and "__ALL__" not in supervisor_districts:
        requests = [r for r in requests if r.requested_district in supervisor_districts]

    return requests


@router.post("/access-requests/{id}/approve")
async def approve_access_request(
    id: int,
    body: AccessRequestReview,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Approve a temporary access request and issue a TemporaryDistrictPermission."""
    check_perm = require_permission(Permission.APPROVE_ACCESS_REQUESTS)
    await check_perm(current_user)

    stmt = select(DistrictAccessRequest).where(DistrictAccessRequest.id == id)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Access request not found.")

    if req.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot approve request in '{req.status}' state.")

    # Enforce supervisor boundary check
    await verify_supervisor_scope(current_user, req.requested_district, db)

    now = datetime.datetime.utcnow()
    req.status = "APPROVED"
    req.reviewed_by = current_user.get("id")
    req.reviewed_at = now
    req.review_comment = body.review_comment

    # Create temporary permission
    permission = TemporaryDistrictPermission(
        user_id=req.requester_id,
        district=req.requested_district,
        access_request_id=req.id,
        approved_by=current_user.get("id"),
        approved_at=now,
        expires_at=now + datetime.timedelta(hours=req.duration_hours),
        related_case_id=req.related_case_id,
        is_revoked=False
    )
    db.add(permission)
    await db.commit()
    await db.refresh(permission)

    # Log security audit
    audit = AuditAgent()
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=f"/api/v1/security/access-requests/{id}/approve",
        request_id=f"app-{uuid.uuid4()}",
        action="APPROVE_ACCESS_REQUEST",
        target_user_id=req.requester_id,
        supervisor_id=current_user.get("id"),
        district_id=req.requested_district,
        case_id=req.related_case_id,
        reason=body.review_comment,
        summary=f"Approved temporary access for user ID {req.requester_id} in district '{req.requested_district}'"
    )

    return {"status": "success", "message": "Access request approved successfully.", "permission": permission}


@router.post("/access-requests/{id}/reject")
async def reject_access_request(
    id: int,
    body: AccessRequestReview,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reject a temporary access request."""
    check_perm = require_permission(Permission.APPROVE_ACCESS_REQUESTS)
    await check_perm(current_user)

    stmt = select(DistrictAccessRequest).where(DistrictAccessRequest.id == id)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Access request not found.")

    if req.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Cannot reject request in '{req.status}' state.")

    # Enforce supervisor boundary check
    await verify_supervisor_scope(current_user, req.requested_district, db)

    req.status = "REJECTED"
    req.reviewed_by = current_user.get("id")
    req.reviewed_at = datetime.datetime.utcnow()
    req.review_comment = body.review_comment
    await db.commit()

    # Log security audit
    audit = AuditAgent()
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=f"/api/v1/security/access-requests/{id}/reject",
        request_id=f"rej-{uuid.uuid4()}",
        action="REJECT_ACCESS_REQUEST",
        target_user_id=req.requester_id,
        supervisor_id=current_user.get("id"),
        district_id=req.requested_district,
        reason=body.review_comment,
        summary=f"Rejected temporary access for user ID {req.requester_id} in district '{req.requested_district}'"
    )

    return {"status": "success", "message": "Access request rejected successfully."}


@router.post("/access-requests/{id}/more-info")
async def more_info_access_request(
    id: int,
    body: AccessRequestReview,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark an access request as requiring more information."""
    check_perm = require_permission(Permission.APPROVE_ACCESS_REQUESTS)
    await check_perm(current_user)

    stmt = select(DistrictAccessRequest).where(DistrictAccessRequest.id == id)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Access request not found.")

    if req.status != "PENDING":
        raise HTTPException(status_code=400, detail="Cannot request more info on already processed request.")

    # Enforce supervisor boundary check
    await verify_supervisor_scope(current_user, req.requested_district, db)

    req.status = "MORE_INFO_REQUIRED"
    req.reviewed_by = current_user.get("id")
    req.reviewed_at = datetime.datetime.utcnow()
    req.review_comment = body.review_comment
    await db.commit()

    return {"status": "success", "message": "Access request updated to MORE_INFO_REQUIRED."}


@router.post("/permissions/{id}/revoke")
async def revoke_temporary_permission(
    id: int,
    body: AccessRequestReview,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Revoke an active temporary permission dynamically."""
    check_perm = require_permission(Permission.APPROVE_ACCESS_REQUESTS)
    await check_perm(current_user)

    stmt = select(TemporaryDistrictPermission).where(
        TemporaryDistrictPermission.id == id,
        TemporaryDistrictPermission.is_revoked == False
    )
    result = await db.execute(stmt)
    perm = result.scalar_one_or_none()
    if not perm:
        raise HTTPException(status_code=404, detail="Active temporary permission not found.")

    # Enforce supervisor boundary check
    await verify_supervisor_scope(current_user, perm.district, db)

    now = datetime.datetime.utcnow()
    perm.is_revoked = True
    perm.revoked_at = now
    perm.revoked_by = current_user.get("id")
    perm.revocation_reason = body.review_comment
    await db.commit()

    # Log security audit
    audit = AuditAgent()
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=f"/api/v1/security/permissions/{id}/revoke",
        request_id=f"rev-{uuid.uuid4()}",
        action="REVOKE_TEMPORARY_ACCESS",
        target_user_id=perm.user_id,
        supervisor_id=current_user.get("id"),
        district_id=perm.district,
        reason=body.review_comment,
        summary=f"Revoked temporary access for user ID {perm.user_id} in district '{perm.district}'"
    )

    return {"status": "success", "message": "Temporary permission revoked successfully."}


# ---------------------------------------------------------------------------
# 2. Permanent District Assignment Management
# ---------------------------------------------------------------------------

@router.get("/district-assignments/investigators")
async def get_all_investigator_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all active investigator/analyst permanent assignments."""
    # Restrict to managers or auditable roles
    role = normalize_role(current_user.get("role"))
    if role not in ("ADMINISTRATOR", "SUPERVISOR"):
        raise HTTPException(status_code=403, detail="Not authorized to view district assignments.")

    supervisor_districts = await get_user_authorized_districts(current_user, db)

    stmt = select(UserDistrictAssignment, User.username, User.role).join(
        User, UserDistrictAssignment.user_id == User.id
    ).where(UserDistrictAssignment.is_active == True)

    if role == "SUPERVISOR":
        stmt = stmt.where(
            User.role.notin_(["SUPERVISOR", "ADMINISTRATOR", "supervisor", "administrator", "admin", "ADMIN"])
        )

    result = await db.execute(stmt)
    records = []
    for row in result.all():
        assignment, username, user_role = row
        records.append({
            "id": assignment.id,
            "user_id": assignment.user_id,
            "username": username,
            "role": user_role,
            "district": assignment.district,
            "assigned_at": assignment.assigned_at
        })

    # Scope filtering if Supervisor
    if role == "SUPERVISOR" and "__ALL__" not in supervisor_districts:
        records = [r for r in records if r["district"] in supervisor_districts]

    return records


@router.get("/district-assignments/user/{user_id}")
async def get_assignments_for_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Retrieve active district assignments for a specific user ID."""
    role = normalize_role(current_user.get("role"))
    if role not in ("ADMINISTRATOR", "SUPERVISOR"):
        raise HTTPException(status_code=403, detail="Not authorized to view district assignments.")

    stmt = select(UserDistrictAssignment).where(
        UserDistrictAssignment.user_id == user_id,
        UserDistrictAssignment.is_active == True
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/district-assignments")
async def create_district_assignment(
    body: DistrictAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new permanent district assignment."""
    check_perm = require_permission(Permission.ASSIGN_DISTRICTS)
    await check_perm(current_user)

    # Enforce supervisor boundary check
    await verify_supervisor_scope(current_user, body.district, db)

    # Check target user
    stmt_user = select(User).where(User.id == body.user_id)
    res_user = await db.execute(stmt_user)
    target_user = res_user.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found.")

    role = normalize_role(current_user.get("role"))
    if role == "SUPERVISOR":
        # 1. Prevent supervisor from assigning themselves
        if body.user_id == current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors cannot assign districts to themselves."
            )
        # 2. Prevent supervisor from assigning to other supervisors or admins
        target_role = normalize_role(target_user.role)
        if target_role in ("SUPERVISOR", "ADMINISTRATOR"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors cannot manage assignments for other Supervisors or Administrators."
            )

    # Prevent duplicate active assignments programmatically (enforces unique partial constraint)
    stmt_chk = select(UserDistrictAssignment).where(
        UserDistrictAssignment.user_id == body.user_id,
        UserDistrictAssignment.district == body.district,
        UserDistrictAssignment.is_active == True
    )
    res_chk = await db.execute(stmt_chk)
    existing = res_chk.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"User already has an active assignment for '{body.district}'.")

    assignment = UserDistrictAssignment(
        user_id=body.user_id,
        district=body.district,
        assigned_by=current_user.get("id"),
        assigned_at=datetime.datetime.utcnow(),
        is_active=True
    )
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    # Log security audit
    audit = AuditAgent()
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api="/api/v1/security/district-assignments",
        request_id=f"asn-{uuid.uuid4()}",
        action="ASSIGN_DISTRICT",
        target_user_id=body.user_id,
        supervisor_id=current_user.get("id"),
        district_id=body.district,
        summary=f"Assigned user ID {body.user_id} permanently to district '{body.district}'"
    )

    return assignment


@router.delete("/district-assignments/{id}")
async def delete_district_assignment(
    id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Deactivate/remove an active permanent assignment."""
    check_perm = require_permission(Permission.ASSIGN_DISTRICTS)
    await check_perm(current_user)

    stmt = select(UserDistrictAssignment).where(
        UserDistrictAssignment.id == id,
        UserDistrictAssignment.is_active == True
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Active district assignment not found.")

    # Enforce supervisor boundary check
    await verify_supervisor_scope(current_user, assignment.district, db)

    role = normalize_role(current_user.get("role"))
    if role == "SUPERVISOR":
        stmt_target = select(User.role).where(User.id == assignment.user_id)
        res_target = await db.execute(stmt_target)
        target_role = normalize_role(res_target.scalar_one_or_none())
        if target_role in ("SUPERVISOR", "ADMINISTRATOR"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors cannot delete assignments for other Supervisors or Administrators."
            )

    assignment.is_active = False
    assignment.removed_at = datetime.datetime.utcnow()
    assignment.removed_by = current_user.get("id")
    await db.commit()

    # Log security audit
    audit = AuditAgent()
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=f"/api/v1/security/district-assignments/{id}",
        request_id=f"rev-{uuid.uuid4()}",
        action="REVOKE_DISTRICT_ASSIGNMENT",
        target_user_id=assignment.user_id,
        supervisor_id=current_user.get("id"),
        district_id=assignment.district,
        summary=f"Revoked permanent assignment to district '{assignment.district}' for user ID {assignment.user_id}"
    )

    return {"status": "success", "message": "District assignment deactivated."}


@router.post("/district-assignments/{id}/reassign")
async def reassign_district(
    id: int,
    body: ReassignBody,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Reassign an investigator from one district to another."""
    check_perm = require_permission(Permission.ASSIGN_DISTRICTS)
    await check_perm(current_user)

    stmt = select(UserDistrictAssignment).where(
        UserDistrictAssignment.id == id,
        UserDistrictAssignment.is_active == True
    )
    result = await db.execute(stmt)
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Active district assignment not found.")

    # Enforce supervisor boundary check on old AND new district
    await verify_supervisor_scope(current_user, assignment.district, db)
    await verify_supervisor_scope(current_user, body.new_district, db)

    role = normalize_role(current_user.get("role"))
    if role == "SUPERVISOR":
        # 1. Prevent reassigning themselves
        if assignment.user_id == current_user.get("id"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors cannot reassign themselves."
            )
        # 2. Prevent reassigning other supervisors/admins
        stmt_target = select(User.role).where(User.id == assignment.user_id)
        res_target = await db.execute(stmt_target)
        target_role = normalize_role(res_target.scalar_one_or_none())
        if target_role in ("SUPERVISOR", "ADMINISTRATOR"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Supervisors cannot reassign other Supervisors or Administrators."
            )

    now = datetime.datetime.utcnow()
    old_district = assignment.district
    target_user_id = assignment.user_id

    # Deactivate current assignment
    assignment.is_active = False
    assignment.removed_at = now
    assignment.removed_by = current_user.get("id")

    # Create new assignment
    new_assignment = UserDistrictAssignment(
        user_id=target_user_id,
        district=body.new_district,
        assigned_by=current_user.get("id"),
        assigned_at=now,
        is_active=True
    )
    db.add(new_assignment)
    await db.commit()
    await db.refresh(new_assignment)

    # Log security audit
    audit = AuditAgent()
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api=f"/api/v1/security/district-assignments/{id}/reassign",
        request_id=f"rea-{uuid.uuid4()}",
        action="REASSIGN_DISTRICT",
        target_user_id=target_user_id,
        supervisor_id=current_user.get("id"),
        district_id=body.new_district,
        reason=f"Reassigned from {old_district} to {body.new_district}",
        summary=f"Reassigned user ID {target_user_id} from district '{old_district}' to '{body.new_district}'"
    )

    return {"status": "success", "message": f"Successfully reassigned user from '{old_district}' to '{body.new_district}'.", "new_assignment": new_assignment}
