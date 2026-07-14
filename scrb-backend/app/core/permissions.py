from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from app.core.rbac import check_permission
from typing import Callable


def require_permission(permission: str) -> Callable:
    """Dependency that requires a user to have a specific permission."""
    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        role = current_user.get("role")
        if not check_permission(role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Role '{role}' does not have '{permission}' permission.",
            )
        return current_user
    return dependency


def verify_district_access(user: dict, district: str | None) -> str | None:
    """
    ABAC validator for district level data containment.
    
    Enforces:
    - Supervisor / Admin / Policymaker: Can view all districts (returns target or None).
    - Senior Investigator: Can view multiple assigned districts.
    - Investigator: Can only view their single assigned district.
    
    If the requested district is None/empty:
    - Auto-inject the user's primary district if they have restricted access.
    - Allow None/All if they have global access.
    
    Raises 403 Forbidden if accessing an unauthorized district.
    """
    role = user.get("role")
    assigned_str = user.get("districts")
    
    # Unrestricted roles
    if role in ("Admin", "Administrator", "Supervisor", "Policy Maker", "Policymaker"):
        return district
        
    if not assigned_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied. User has no assigned districts.",
        )
        
    assigned_list = [d.strip().lower() for d in assigned_str.split(",") if d.strip()]
    
    if not district or district.lower() == "all":
        # If unrestricted view is requested by restricted user, limit to their first assigned district
        return assigned_str.split(",")[0].strip()
        
    if district.lower() not in assigned_list:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied. You are not authorized to view data for district '{district}'. Assigned: {assigned_str}",
        )
        
    return district
