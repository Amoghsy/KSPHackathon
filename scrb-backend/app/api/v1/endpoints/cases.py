from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.case import CaseService

router = APIRouter()


@router.get("/")
async def get_cases(
    q: str | None = None,
    status: str | None = None,
    district: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=15, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve cases list with query, status, district filters and pagination."""
    service = CaseService(db)
    result = await service.list_cases_paginated(
        q=q, status=status, district=district, page=page, page_size=pageSize
    )
    return result


@router.get("/{id}")
async def get_case_by_id(id: int, db: AsyncSession = Depends(get_db)):
    """Retrieve specific case parameters by ID."""
    service = CaseService(db)
    case_detail = await service.get_case_detail(id)
    if not case_detail:
        raise HTTPException(status_code=404, detail=f"Case with ID {id} not found.")
    return case_detail
