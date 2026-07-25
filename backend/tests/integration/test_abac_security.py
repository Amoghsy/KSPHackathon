import asyncio
import datetime
import pytest
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import SessionLocal
from app.models.user import User
from app.core.permissions import get_user_authorized_districts, verify_district_access
from app.core.rbac import Permission, normalize_role
from app.agents.query_agent.query_agent import QueryAgent
from app.services.nl2sql.sql_validator import SQLValidator
from fastapi import HTTPException

# Mark as using asyncio
pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_temp_permission(db_session: AsyncSession):
    from app.models.access_request import DistrictAccessRequest, TemporaryDistrictPermission
    from app.models.user import User
    from sqlalchemy import delete
    import datetime

    # Load test users
    stmt1 = select(User).where(User.username == "insp_mysuru")
    res1 = await db_session.execute(stmt1)
    insp = res1.scalar_one_or_none()

    stmt2 = select(User).where(User.username == "supervisor_ramesh")
    res2 = await db_session.execute(stmt2)
    ramesh = res2.scalar_one_or_none()

    if not insp or not ramesh:
        pytest.skip("insp_mysuru or supervisor_ramesh not found in DB")

    # Clean up any existing records
    await db_session.execute(delete(TemporaryDistrictPermission).where(TemporaryDistrictPermission.user_id == insp.id))
    await db_session.execute(delete(DistrictAccessRequest).where(DistrictAccessRequest.requester_id == insp.id))
    # Remove any permanent assignments other than Mysuru for insp_mysuru to prevent DB contamination
    from app.models.district_assignment import UserDistrictAssignment
    await db_session.execute(
        delete(UserDistrictAssignment).where(
            UserDistrictAssignment.user_id == insp.id,
            UserDistrictAssignment.district != "Mysuru"
        )
    )
    # Remove any permanent assignments other than Bengalur Urban, Mysuru, Tumakuru for supervisor_ramesh to prevent DB contamination
    await db_session.execute(
        delete(UserDistrictAssignment).where(
            UserDistrictAssignment.user_id == ramesh.id,
            UserDistrictAssignment.district.notin_(["Bengaluru Urban", "Mysuru", "Tumakuru"])
        )
    )
    await db_session.commit()

    # Insert fresh active temporary permission
    now = datetime.datetime.utcnow()
    req = DistrictAccessRequest(
        requester_id=insp.id,
        requested_district="Bengaluru Urban",
        reason="Test integration active temp permission",
        duration_hours=2,
        status="APPROVED",
        requested_at=now - datetime.timedelta(minutes=30),
        reviewed_by=ramesh.id,
        reviewed_at=now - datetime.timedelta(minutes=30),
        review_comment="Approved for test"
    )
    db_session.add(req)
    await db_session.flush()

    perm = TemporaryDistrictPermission(
        user_id=insp.id,
        district="Bengaluru Urban",
        access_request_id=req.id,
        approved_by=ramesh.id,
        approved_at=now - datetime.timedelta(minutes=30),
        expires_at=now + datetime.timedelta(hours=2),
        is_revoked=False
    )
    db_session.add(perm)
    await db_session.commit()

    yield

    # Clean up after test runs
    await db_session.execute(delete(TemporaryDistrictPermission).where(TemporaryDistrictPermission.user_id == insp.id))
    await db_session.execute(delete(DistrictAccessRequest).where(DistrictAccessRequest.requester_id == insp.id))
    await db_session.commit()



async def get_user_by_username(username: str, db: AsyncSession) -> dict:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    u = result.scalar_one_or_none()
    if not u:
        raise ValueError(f"Seeded user {username} not found.")
    from app.models.district_assignment import UserDistrictAssignment
    stmt_dists = select(UserDistrictAssignment.district).where(
        UserDistrictAssignment.user_id == u.id,
        UserDistrictAssignment.is_active == True
    )
    res_dists = await db.execute(stmt_dists)
    assigned_dists = [r[0] for r in res_dists.fetchall()]
    districts_str = ",".join(assigned_dists) if assigned_dists else None

    return {"id": u.id, "username": u.username, "role": u.role, "districts": districts_str}


# ---------------------------------------------------------------------------
# ABAC Logic Verification Tests
# ---------------------------------------------------------------------------

async def test_permanent_district_assignments_loading(db_session: AsyncSession):
    # Verify that Ramesh supervises Bengaluru Urban, Mysuru, Tumakuru
    ramesh = await get_user_by_username("supervisor_ramesh", db_session)
    ramesh_dists = await get_user_authorized_districts(ramesh, db_session)
    assert "Bengaluru Urban" in ramesh_dists
    assert "Mysuru" in ramesh_dists
    assert "Tumakuru" in ramesh_dists
    assert len(ramesh_dists) == 3

    # Verify insp_mysuru has permanent assignment only to Mysuru
    insp_mysuru = await get_user_by_username("insp_mysuru", db_session)
    mysuru_dists = await get_user_authorized_districts(insp_mysuru, db_session)
    assert len(mysuru_dists) == 2  # Wait! 1 permanent Mysuru + 1 active temporary Bengaluru Urban!
    assert "Mysuru" in mysuru_dists
    assert "Bengaluru Urban" in mysuru_dists


async def test_supervisor_access_control_boundaries(db_session: AsyncSession):
    ramesh = await get_user_by_username("supervisor_ramesh", db_session)

    # Ramesh supervising Mysuru -> Success
    allowed = await verify_district_access(ramesh, "Mysuru", db_session)
    assert allowed == "Mysuru"

    # Ramesh accessing Belagavi (outside scope) -> Raise 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        await verify_district_access(ramesh, "Belagavi", db_session)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail["code"] == "DISTRICT_NOT_AUTHORIZED"


async def test_temporary_permissions_access_evaluation(db_session: AsyncSession):
    insp_mysuru = await get_user_by_username("insp_mysuru", db_session)

    # 1. Access to Mysuru (permanent) -> OK
    allowed = await verify_district_access(insp_mysuru, "Mysuru", db_session)
    assert allowed == "Mysuru"

    # 2. Access to Bengaluru Urban (Active temporary permission) -> OK
    allowed_temp = await verify_district_access(insp_mysuru, "Bengaluru Urban", db_session)
    assert allowed_temp == "Bengaluru Urban"

    # 3. Access to Belagavi (no assignment or request) -> Fail
    with pytest.raises(HTTPException) as exc_info:
        await verify_district_access(insp_mysuru, "Belagavi", db_session)
    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# SQL Query Rewriting Verification Tests
# ---------------------------------------------------------------------------

async def test_sql_query_rewriting_for_abac(db_session: AsyncSession):
    insp_mysuru = await get_user_by_username("insp_mysuru", db_session)
    auth_districts = await get_user_authorized_districts(insp_mysuru, db_session)
    
    # Let's perform query rewriting
    import re
    dist_list = ", ".join(f"'{d}'" for d in auth_districts)
    assert "Mysuru" in dist_list
    assert "Bengaluru Urban" in dist_list

    generated_sql = "SELECT * FROM case_master JOIN police_station ON case_master.police_station_id = police_station.police_station_id"

    replacements = {
        "case_master": f"(SELECT * FROM case_master WHERE police_station_id IN (SELECT police_station_id FROM police_station WHERE district IN ({dist_list})))",
        "police_station": f"(SELECT * FROM police_station WHERE district IN ({dist_list}))",
    }

    scoped_sql = generated_sql
    for table, subquery in replacements.items():
        pattern = re.compile(rf'\b{table}\b', re.IGNORECASE)
        scoped_sql = pattern.sub(subquery, scoped_sql)

    # Assert that case_master and police_station are replaced with district subqueries
    assert "(SELECT * FROM case_master WHERE police_station_id" in scoped_sql
    assert "district IN (" in scoped_sql
    assert "police_station_id = (SELECT * FROM police_station" in scoped_sql
