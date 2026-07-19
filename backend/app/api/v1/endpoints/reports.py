import csv
import uuid
import datetime
from io import BytesIO, StringIO
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import get_current_user
from app.core.permissions import require_permission, verify_district_access
from app.core.rbac import Permission
from app.services.case import CaseService
from app.agents.audit_agent.audit_agent import AuditAgent

router = APIRouter()


@router.get("/export/csv")
async def export_csv(
    district: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Export case listings as a CSV file.
    Enforces district ABAC and logs a security audit event.
    """
    check_perm = require_permission(Permission.EXPORT_REPORTS)
    await check_perm(current_user)

    # ABAC: Enforce district access containment
    allowed_district = await verify_district_access(current_user, district, db)

    # Log to Audit Log
    audit = AuditAgent()
    req_id = f"export-{uuid.uuid4()}"
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api="/api/v1/reports/export/csv",
        request_id=req_id,
        action="EXPORT_REPORTS_CSV",
        district_id=allowed_district,
        summary=f"Exported case database as CSV for district {allowed_district or 'All'}"
    )

    service = CaseService(db)
    result = await service.list_cases_paginated(district=allowed_district, page=1, page_size=200)
    items = result.get("items", [])

    f = StringIO()
    writer = csv.writer(f)
    # Header
    writer.writerow(["ID", "Crime No", "Case No", "Date", "Police Station", "District", "Crime Head", "Status", "Gravity"])
    
    for item in items:
        writer.writerow([
            item.get("id"),
            item.get("crimeNo"),
            item.get("caseNo"),
            item.get("date"),
            item.get("station"),
            item.get("district"),
            item.get("crimeHead"),
            item.get("status"),
            item.get("gravity")
        ])

    f.seek(0)
    response = StreamingResponse(
        iter([f.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=investigation_report.csv"}
    )
    return response


@router.get("/export/pdf")
async def export_pdf(
    district: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Generates a structured text/markdown report of the current investigation state.
    Enforces district ABAC and logs a security audit event.
    """
    check_perm = require_permission(Permission.EXPORT_REPORTS)
    await check_perm(current_user)

    # ABAC: Enforce district access containment
    allowed_district = await verify_district_access(current_user, district, db)

    # Log to Audit Log
    audit = AuditAgent()
    req_id = f"export-{uuid.uuid4()}"
    await audit.log_action(
        db,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        role=current_user.get("role"),
        api="/api/v1/reports/export/pdf",
        request_id=req_id,
        action="EXPORT_REPORTS_PDF",
        district_id=allowed_district,
        summary=f"Exported case database briefing as text file for district {allowed_district or 'All'}"
    )

    service = CaseService(db)
    result = await service.list_cases_paginated(district=allowed_district, page=1, page_size=15)
    items = result.get("items", [])

    report = []
    report.append("=========================================================")
    report.append(" KARNATAKA STATE POLICE — SCRB INTELLIGENCE PLATFORM")
    report.append(" CONFIDENTIAL INVESTIGATION REPORT")
    report.append("=========================================================")
    report.append(f"Exported By: {current_user.get('username')}")
    report.append(f"System Role: {current_user.get('role')}")
    report.append(f"Filter District: {allowed_district or 'All Districts'}")
    report.append("---------------------------------------------------------")
    report.append("\nRECENT REGISTERED CASES SUMMARY:\n")

    for idx, item in enumerate(items, 1):
        report.append(f"{idx}. [{item.get('status')}] Crime No: {item.get('crimeNo')} ({item.get('crimeHead')})")
        report.append(f"   Station: {item.get('station')}, {item.get('district')} District")
        report.append(f"   Narrative: {item.get('narrative')[:120]}...\n")

    report.append("=========================================================")
    report.append("END OF REPORT — GENERATED VIA AUDITED GATEWAY SYSTEM")
    report.append("=========================================================")

    pdf_text = "\n".join(report)
    buf = BytesIO(pdf_text.encode("utf-8"))
    
    response = StreamingResponse(
        buf,
        media_type="text/plain",
        headers={"Content-Disposition": "attachment; filename=investigation_report.txt"}
    )
    return response
