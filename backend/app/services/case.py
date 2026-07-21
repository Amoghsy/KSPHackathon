from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.case import CaseRepository


def map_status(status_id: int | None) -> str:
    # 1: Under Investigation, 2: Charge Sheeted, 3: Closed, 4: Undetected
    mapping = {
        1: "Under Investigation",
        2: "Charge Sheeted",
        3: "Closed",
        4: "Undetected"
    }
    return mapping.get(status_id or 1, "Under Investigation")


def map_gravity(gravity_id: int | None) -> str:
    # 1: Low, 2: Medium, 3: High, 4: Grievous
    mapping = {
        1: "Low",
        2: "Medium",
        3: "High",
        4: "Grievous"
    }
    return mapping.get(gravity_id or 2, "Medium")


class CaseService:
    def __init__(self, db: AsyncSession):
        self.repository = CaseRepository(db)

    async def list_cases(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Basic case list."""
        cases = await self.repository.get_cases(limit, offset)
        return [
            {
                "case_master_id": c.case_master_id,
                "crime_no": c.crime_no,
                "case_no": c.case_no,
                "crime_registered_date": c.crime_registered_date,
                "police_station_id": c.police_station_id,
                "incident_from_date": c.incident_from_date,
                "incident_to_date": c.incident_to_date,
                "latitude": float(c.latitude) if c.latitude is not None else None,
                "longitude": float(c.longitude) if c.longitude is not None else None,
                "brief_facts": c.brief_facts,
            }
            for c in cases
        ]

    async def list_cases_paginated(
        self,
        q: str | None = None,
        status: str | None = None,
        district: str | None = None,
        page: int = 1,
        page_size: int = 15,
    ) -> dict:
        """Fetch and format paginated cases for the Case Search page."""
        # Reverse status mapping
        status_id = None
        if status and status != "All":
            status_mappings = {
                "Under Investigation": 1,
                "Charge Sheeted": 2,
                "Closed": 3,
                "Undetected": 4
            }
            status_id = status_mappings.get(status)

        district_clean = None
        if district and district != "All":
            district_clean = district

        offset = (page - 1) * page_size
        cases = await self.repository.get_filtered_cases(
            q=q,
            status_id=status_id,
            district=district_clean,
            limit=page_size,
            offset=offset,
        )
        total = await self.repository.get_filtered_cases_count(
            q=q, status_id=status_id, district=district_clean
        )

        formatted_items = []
        for c in cases:
            formatted_items.append({
                "id": str(c.case_master_id),
                "crimeNo": c.crime_no,
                "caseNo": c.case_no or f"C-{c.case_master_id}",
                "date": c.crime_registered_date.strftime("%d %b %Y") if c.crime_registered_date else "Unknown",
                "station": c.police_station.name if c.police_station else "Unknown PS",
                "district": c.police_station.district if c.police_station else "Unknown District",
                "crimeHead": c.crime_type.name if c.crime_type else "General Crime",
                "status": map_status(c.case_status_id),
                "gravity": map_gravity(c.gravity_offence_id),
                "narrative": c.brief_facts or "",
                "victimName": c.victims[0].victim_name if c.victims else None,
                "complainant": c.complainants[0].complainant_name if c.complainants else "State of Karnataka",
            })

        return {
            "items": formatted_items,
            "total": total
        }

    async def get_case_detail(self, case_id: int) -> dict | None:
        """Fetch detailed case parameters for Case Details page."""
        c = await self.repository.get_case_by_id(case_id)
        if not c:
            return None

        # Build list of accused
        accused_list = []
        for a in c.accused:
            accused_list.append({
                "id": str(a.accused_master_id),
                "name": a.accused_name or "Unknown Accused",
                "age": a.age_year or 30,
                "gender": "Male" if a.gender_id == 1 else "Female",
            })

        # Build list of victims
        victims_list = []
        for v in c.victims:
            victims_list.append({
                "id": str(v.victim_master_id),
                "name": v.victim_name or "Unknown Victim",
                "age": v.age_year or 30,
                "gender": "Male" if v.gender_id == 1 else "Female",
            })

        # Complainant Details from database
        comp_obj = c.complainants[0] if c.complainants else None
        complainant_name = comp_obj.complainant_name if comp_obj else "State of Karnataka"
        complainant_caste = comp_obj.caste.caste_master_name if comp_obj and comp_obj.caste else "General Category"
        complainant_religion = comp_obj.religion.religion_name if comp_obj and comp_obj.religion else "Category A"
        complainant_occupation = comp_obj.occupation.occupation_name if comp_obj and comp_obj.occupation else "Service"
        complainant_age = comp_obj.age_year if comp_obj else 35
        complainant_gender = "Male" if comp_obj and comp_obj.gender_id == 1 else "Female" if comp_obj and comp_obj.gender_id == 2 else "Transgender"

        return {
            "id": str(c.case_master_id),
            "crimeNo": c.crime_no,
            "caseNo": c.case_no or f"C-{c.case_master_id}",
            "date": c.crime_registered_date.strftime("%d %b %Y") if c.crime_registered_date else "Unknown",
            "station": c.police_station.name if c.police_station else "Unknown PS",
            "district": c.police_station.district if c.police_station else "Unknown District",
            "crimeHead": c.crime_type.name if c.crime_type else "General Crime",
            "complainant": complainant_name,
            "complainantCaste": complainant_caste,
            "complainantReligion": complainant_religion,
            "complainantOccupation": complainant_occupation,
            "complainantAge": complainant_age,
            "complainantGender": complainant_gender,
            "status": map_status(c.case_status_id),
            "gravity": map_gravity(c.gravity_offence_id),
            "narrative": c.brief_facts or "",
            "accused": accused_list,
            "victims": victims_list,
            "actsSections": ["IPC Section 379", "IPC Section 34"],
            "timeline": [
                {
                    "title": "FIR Registered",
                    "date": c.crime_registered_date.strftime("%d %b %Y") if c.crime_registered_date else "Unknown",
                    "description": "Case filed in police record."
                }
            ],
        }

    async def get_metadata(self) -> dict:
        """Fetch unique/distinct districts and crime types from the DB, alongside static statuses/gravity."""
        from sqlalchemy import select
        from app.models.police_station import PoliceStation
        from app.models.crime_type import CrimeType

        # Get unique districts from PoliceStation
        districts_stmt = select(PoliceStation.district).where(PoliceStation.district.is_not(None)).distinct()
        districts_res = await self.repository.db.execute(districts_stmt)
        districts = sorted([r[0] for r in districts_res.all() if r[0]])

        # Get unique crime heads from CrimeType
        crime_types_stmt = select(CrimeType.name).where(CrimeType.name.is_not(None)).distinct()
        crime_types_res = await self.repository.db.execute(crime_types_stmt)
        crime_types = sorted([r[0] for r in crime_types_res.all() if r[0]])

        return {
            "districts": districts,
            "crime_heads": crime_types,
            "statuses": ["Under Investigation", "Charge Sheeted", "Closed", "Undetected"],
            "gravity": ["Low", "Medium", "High", "Grievous"]
        }
