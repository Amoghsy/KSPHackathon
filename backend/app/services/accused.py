from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.accused import AccusedRepository
from app.services.case import map_status


class AccusedService:
    def __init__(self, db: AsyncSession):
        self.repository = AccusedRepository(db)

    async def list_accused(self, limit: int = 100, offset: int = 0) -> list[dict]:
        """Basic list of accused."""
        accused = await self.repository.get_accused(limit, offset)
        return [
            {
                "accused_master_id": a.accused_master_id,
                "case_master_id": a.case_master_id,
                "accused_name": a.accused_name,
                "age_year": a.age_year,
                "gender_id": a.gender_id,
                "person_id": a.person_id,
            }
            for a in accused
        ]

    async def list_offenders_paginated(
        self, q: str | None = None, page: int = 1, page_size: int = 15
    ) -> dict:
        """Fetch distinct repeat offenders with pagination, modus operandi, and risk scores."""
        offset = (page - 1) * page_size
        unique_offenders = await self.repository.get_unique_offenders(
            q=q, limit=page_size, offset=offset
        )
        total = await self.repository.get_unique_offenders_count(q=q)

        items = []
        for a in unique_offenders:
            # Fetch all cases for this offender to calculate counts and Mo
            instances = await self.repository.get_all_instances_by_person_id(a.person_id)
            cases = [inst.case for inst in instances if inst.case]
            
            linked_cases_count = len(cases)
            risk_score = min(100, linked_cases_count * 25)
            
            # Risk label
            if risk_score > 70:
                risk_label = "High"
            elif risk_score > 40:
                risk_label = "Medium"
            else:
                risk_label = "Low"
                
            modus_operandi = list(set(c.crime_type.name for c in cases if c.crime_type))
            if not modus_operandi:
                modus_operandi = ["General Crime"]
                
            last_known = "Bengaluru"
            if cases and cases[0].police_station:
                last_known = cases[0].police_station.district

            items.append({
                "id": StringOrId(a.person_id or str(a.accused_master_id)),
                "name": a.accused_name or "Unknown Accused",
                "age": a.age_year or 30,
                "linkedCases": linked_cases_count,
                "riskScore": risk_score,
                "risk": risk_label,
                "modusOperandi": modus_operandi[:3],
                "aliases": [],
                "lastKnown": last_known,
                "factors": [
                    {"label": "Prior Convictions", "value": min(100, linked_cases_count * 20)},
                    {"label": "Case Severity", "value": int(risk_score * 0.8)}
                ]
            })

        return {
            "items": items,
            "total": total
        }

    async def get_offender_detail(self, offender_id: str) -> dict | None:
        """Fetch full details, historical offenses, risk factors, and associates of a suspect."""
        # Check if ID is accused_master_id (int) or unique person_id (str)
        person_id = offender_id
        acc_name = "Unknown Accused"
        age = 30
        gender_id = 1
        accused_master_id = None

        try:
            numeric_id = int(offender_id)
            acc_master = await self.repository.get_by_master_id(numeric_id)
            if acc_master:
                person_id = acc_master.person_id
                acc_name = acc_master.accused_name
                age = acc_master.age_year
                gender_id = acc_master.gender_id
                accused_master_id = acc_master.accused_master_id
        except ValueError:
            pass

        # Load all database instances for this person_id
        instances = await self.repository.get_all_instances_by_person_id(person_id)
        if not instances:
            # Fallback in case person_id search fails but we have master info
            if accused_master_id:
                instances = [acc_master]
            else:
                return None

        # Core details from the first instance
        core_acc = instances[0]
        acc_name = core_acc.accused_name or acc_name
        age = core_acc.age_year or age
        gender_id = core_acc.gender_id or gender_id

        cases = [inst.case for inst in instances if inst.case]
        linked_cases_count = len(cases)
        
        # Calculate dynamic risk score
        risk_score = min(100, linked_cases_count * 25)
        
        districts = set()
        for c in cases:
            if c.police_station and c.police_station.district:
                districts.add(c.police_station.district)
        if len(districts) > 1:
            risk_score = min(100, risk_score + 15)

        if risk_score > 70:
            risk_label = "High"
        elif risk_score > 40:
            risk_label = "Medium"
        else:
            risk_label = "Low"

        modus_operandi = list(set(c.crime_type.name for c in cases if c.crime_type))
        if not modus_operandi:
            modus_operandi = ["General Crime"]
            
        last_known = "Bengaluru"
        if cases and cases[0].police_station:
            last_known = cases[0].police_station.district

        # Find known associates (other accused listed on their same cases)
        associates_map = {}
        for c in cases:
            for other_acc in c.accused:
                other_pid = other_acc.person_id
                if other_pid != person_id:
                    if other_pid not in associates_map:
                        associates_map[other_pid] = {
                            "id": other_acc.person_id or str(other_acc.accused_master_id),
                            "name": other_acc.accused_name,
                            "cases": []
                        }
                    associates_map[other_pid]["cases"].append(c.crime_no)

        formatted_cases = []
        for c in cases:
            formatted_cases.append({
                "id": str(c.case_master_id),
                "crimeNo": c.crime_no,
                "caseNo": c.case_no or f"C-{c.case_master_id}",
                "date": c.crime_registered_date.strftime("%d %b %Y") if c.crime_registered_date else "Unknown",
                "station": c.police_station.name if c.police_station else "Unknown PS",
                "status": map_status(c.case_status_id)
            })

        return {
            "id": person_id,
            "name": acc_name,
            "age": age,
            "gender": "Male" if gender_id == 1 else "Female",
            "linkedCases": linked_cases_count,
            "riskScore": risk_score,
            "risk": risk_label,
            "modusOperandi": modus_operandi,
            "aliases": [f"Alias {acc_name.split()[0]}"] if len(acc_name.split()) > 0 else [],
            "lastKnown": last_known,
            "factors": [
                {"label": "Prior Convictions", "value": min(100, linked_cases_count * 20)},
                {"label": "Case Severity", "value": int(risk_score * 0.8)},
                {"label": "Cross-District Operations", "value": 75 if len(districts) > 1 else 10}
            ],
            "cases": formatted_cases,
            "associates": list(associates_map.values())
        }


def StringOrId(val: str | None) -> str:
    return str(val) if val is not None else ""
