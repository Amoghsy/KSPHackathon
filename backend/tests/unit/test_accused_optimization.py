import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.accused import AccusedService

@pytest.mark.asyncio
async def test_list_offenders_paginated_optimisation():
    # Mock db and repository
    db_mock = MagicMock()
    service = AccusedService(db_mock)
    service.repository = MagicMock()
    
    # Create fake unique offenders
    accused_1 = MagicMock()
    accused_1.person_id = "PID001"
    accused_1.accused_master_id = 1
    accused_1.accused_name = "Offender One"
    accused_1.age_year = 25
    accused_1.gender_id = 1

    accused_2 = MagicMock()
    accused_2.person_id = "PID002"
    accused_2.accused_master_id = 2
    accused_2.accused_name = "Offender Two"
    accused_2.age_year = 35
    accused_2.gender_id = 2

    service.repository.get_unique_offenders = AsyncMock(return_value=[accused_1, accused_2])
    service.repository.get_unique_offenders_count = AsyncMock(return_value=2)

    # Create fake historical instances for the offenders
    instance_1 = MagicMock()
    instance_1.person_id = "PID001"
    instance_1.accused_name = "Offender One"
    instance_1.age_year = 25
    instance_1.gender_id = 1
    
    case_1 = MagicMock()
    case_1.case_master_id = 101
    case_1.crime_no = "CRIME101"
    case_1.crime_type = MagicMock()
    case_1.crime_type.name = "Theft"
    case_1.police_station = MagicMock()
    case_1.police_station.district = "Bengaluru"
    instance_1.case = case_1

    instance_2 = MagicMock()
    instance_2.person_id = "PID002"
    instance_2.accused_name = "Offender Two"
    instance_2.age_year = 35
    instance_2.gender_id = 2
    
    case_2 = MagicMock()
    case_2.case_master_id = 102
    case_2.crime_no = "CRIME102"
    case_2.crime_type = MagicMock()
    case_2.crime_type.name = "Robbery"
    case_2.police_station = MagicMock()
    case_2.police_station.district = "Mysuru"
    instance_2.case = case_2

    service.repository.get_all_instances_by_person_ids = AsyncMock(return_value=[instance_1, instance_2])

    result = await service.list_offenders_paginated(page=1, page_size=2)

    # Verify repository calls
    service.repository.get_unique_offenders.assert_called_once_with(
        q=None, limit=2, offset=0, authorized_districts=None
    )
    service.repository.get_unique_offenders_count.assert_called_once_with(
        q=None, authorized_districts=None
    )
    service.repository.get_all_instances_by_person_ids.assert_called_once_with(["PID001", "PID002"])

    # Verify outputs
    assert result["total"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["id"] == "PID001"
    assert result["items"][0]["name"] == "Offender One"
    assert result["items"][0]["linkedCases"] == 1
    assert result["items"][0]["modusOperandi"] == ["Theft"]
    assert result["items"][0]["lastKnown"] == "Bengaluru"

    assert result["items"][1]["id"] == "PID002"
    assert result["items"][1]["name"] == "Offender Two"
    assert result["items"][1]["linkedCases"] == 1
    assert result["items"][1]["modusOperandi"] == ["Robbery"]
    assert result["items"][1]["lastKnown"] == "Mysuru"
