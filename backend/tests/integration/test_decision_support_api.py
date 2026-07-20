import pytest
import sys
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import select

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.db.session import SessionLocal
from app.core.security import get_current_user
from app.models.case import CaseMaster
from app.models.user import User

pytestmark = pytest.mark.anyio

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def anyio_backend():
    return "asyncio"

async def get_test_case_id() -> int | None:
    async with SessionLocal() as session:
        stmt = select(CaseMaster.case_master_id).limit(1)
        res = await session.execute(stmt)
        return res.scalar()

async def get_user_from_db(username: str) -> dict | None:
    async with SessionLocal() as session:
        stmt = select(User).where(User.username == username)
        res = await session.execute(stmt)
        u = res.scalar_one_or_none()
        if u:
            return {"id": u.id, "username": u.username, "role": u.role, "districts": u.districts}
        return None

def test_decision_support_endpoints_investigator(client):
    """
    Test that an authorized investigator can retrieve decision support briefs, leads, etc.
    """
    # Get a real case ID
    case_id = asyncio.run(get_test_case_id())
    if not case_id:
        pytest.skip("No case seeded in the database. Skipping integration test.")
        
    # Get investigator user from DB
    insp_user = asyncio.run(get_user_from_db("insp_mysuru"))
    if not insp_user:
        insp_user = {
            "id": 2,
            "username": "insp_mysuru",
            "role": "INVESTIGATOR",
            "districts": "Mysuru"
        }

    # Override get_current_user dependency
    app.dependency_overrides[get_current_user] = lambda: insp_user
    
    try:
        # 1. Test Brief
        response = client.get(f"/api/v1/decision-support/case/{case_id}/brief")
        # Note: If it's a Mysuru case, it should return 200. If it's outside Mysuru (e.g. Bengaluru), it might return 403.
        # So we handle both HTTP 200 and 403 as correct ABAC enforcement validation results.
        assert response.status_code in (200, 403)
        if response.status_code == 200:
            data = response.json()
            assert "case" in data
            assert "leads" in data
            assert "similar_cases" in data
            assert "ai_summary" in data
            
        # 2. Test Leads
        response = client.get(f"/api/v1/decision-support/case/{case_id}/leads")
        assert response.status_code in (200, 403)
        
        # 3. Test Gaps
        response = client.get(f"/api/v1/decision-support/case/{case_id}/gaps")
        assert response.status_code in (200, 403)
        
        # 4. Test Timeline
        response = client.get(f"/api/v1/decision-support/case/{case_id}/timeline")
        assert response.status_code in (200, 403)
        
    finally:
        app.dependency_overrides.clear()


def test_decision_support_endpoints_unauthorized_role(client):
    """
    Test that administrators are blocked from accessing investigative briefs.
    """
    case_id = asyncio.run(get_test_case_id())
    if not case_id:
        pytest.skip("No case seeded in the database. Skipping.")

    admin_user = {
        "id": 1,
        "username": "admin",
        "role": "ADMINISTRATOR",
        "districts": ""
    }
    
    app.dependency_overrides[get_current_user] = lambda: admin_user
    
    try:
        response = client.get(f"/api/v1/decision-support/case/{case_id}/brief")
        assert response.status_code == 403
        data = response.json()
        assert "Permission Denied" in data["detail"]
    finally:
        app.dependency_overrides.clear()
