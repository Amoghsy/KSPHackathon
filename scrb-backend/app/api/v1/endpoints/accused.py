from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.accused import AccusedService

router = APIRouter()


@router.get("/")
async def get_accused_list(
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=15, ge=1),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve unique repeat offender profiles list with name search and pagination."""
    service = AccusedService(db)
    result = await service.list_offenders_paginated(q=q, page=page, page_size=pageSize)
    return result


@router.get("/{id}")
async def get_offender_by_id(id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed profile of a suspect by ID."""
    service = AccusedService(db)
    profile = await service.get_offender_detail(id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Suspect with ID {id} not found.")
    return profile
