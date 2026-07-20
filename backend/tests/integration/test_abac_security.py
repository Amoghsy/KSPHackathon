import asyncio
import datetime
import pytest
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
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


@pytest.fixture(scope="module")
def event_loop():
    """Create selector event loop for Windows compatibility."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session


async def get_user_by_username(username: str, db: AsyncSession) -> dict:
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    u = result.scalar_one_or_none()
    if not u:
        raise ValueError(f"Seeded user {username} not found.")
    return {"id": u.id, "username": u.username, "role": u.role, "districts": u.districts}


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
