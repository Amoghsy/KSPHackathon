import datetime
from sqlalchemy import func, select, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.models.accused import AccusedMaster


class DashboardRepository:
    def __init__(self, db: AsyncSession, authorized_districts: list[str] | None = None):
        self.db = db
        self.authorized_districts = authorized_districts

    async def get_stats_kpis(self) -> list[dict]:
        """Fetch total active case statistics and build KPIs."""
        cases_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster)
        open_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster).where(CaseMaster.case_status_id == 1)
        closed_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster).where(CaseMaster.case_status_id == 3)
        cs_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster).where(CaseMaster.case_status_id == 2)
        dist_stmt = select(func.count(func.distinct(PoliceStation.district))).select_from(PoliceStation)
        
        if self.authorized_districts is not None:
            cases_stmt = cases_stmt.join(CaseMaster.police_station).where(PoliceStation.district.in_(self.authorized_districts))
            open_stmt = open_stmt.join(CaseMaster.police_station).where(PoliceStation.district.in_(self.authorized_districts))
            closed_stmt = closed_stmt.join(CaseMaster.police_station).where(PoliceStation.district.in_(self.authorized_districts))
            cs_stmt = cs_stmt.join(CaseMaster.police_station).where(PoliceStation.district.in_(self.authorized_districts))
            dist_stmt = dist_stmt.where(PoliceStation.district.in_(self.authorized_districts))

        cases_res = await self.db.execute(cases_stmt)
        open_res = await self.db.execute(open_stmt)
        closed_res = await self.db.execute(closed_stmt)
        cs_res = await self.db.execute(cs_stmt)
        dist_res = await self.db.execute(dist_stmt)
        
        total_cases = cases_res.scalar() or 0
        open_cases = open_res.scalar() or 0
        closed_cases = closed_res.scalar() or 0
        cs_cases = cs_res.scalar() or 0
        districts_active = dist_res.scalar() or 0

        return [
            {"label": "Total Cases", "value": total_cases, "delta": 4.2},
            {"label": "Open Cases", "value": open_cases, "delta": -2.1},
            {"label": "Closed Cases", "value": closed_cases, "delta": 6.8},
            {"label": "Charge-Sheeted", "value": cs_cases, "delta": 3.5},
            {"label": "Districts Active", "value": districts_active, "delta": 0.0}
        ]

    async def get_monthly_trends(self) -> list[dict]:
        """Query case counts grouped by month and crime type (Theft, Robbery, Cybercrime, Assault)."""
        month_trunc = func.date_trunc('month', CaseMaster.crime_registered_date)
        stmt = (
            select(month_trunc.label('month_date'), CrimeType.name, func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .join(CaseMaster.crime_type)
            .group_by(month_trunc, CrimeType.name)
            .order_by(month_trunc)
        )
        
        if self.authorized_districts is not None:
            stmt = stmt.join(CaseMaster.police_station).where(PoliceStation.district.in_(self.authorized_districts))

        res = await self.db.execute(stmt)
        
        pivot = {}
        for row in res.all():
            m_str = row.month_date.strftime("%b %Y") if row.month_date else "Unknown"
            if m_str not in pivot:
                pivot[m_str] = {"month": m_str, "raw_date": row.month_date}
            
            name = row.name
            if name == "Cyber Fraud":
                name = "Cybercrime"
            
            pivot[m_str][name] = row.count

        categories = ["Theft", "Robbery", "Cybercrime", "Assault"]
        for m_data in pivot.values():
            for cat in categories:
                if cat not in m_data:
                    m_data[cat] = 0

        return sorted(list(pivot.values()), key=lambda x: x["raw_date"])

    async def get_district_counts(self, limit: int = 5) -> list[dict]:
        """Fetch district case counts sorted descending."""
        stmt = (
            select(PoliceStation.district, func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .join(CaseMaster.police_station)
            .group_by(PoliceStation.district)
            .order_by(func.count(CaseMaster.case_master_id).desc())
            .limit(limit)
        )
        
        if self.authorized_districts is not None:
            stmt = stmt.where(PoliceStation.district.in_(self.authorized_districts))

        res = await self.db.execute(stmt)
        return [{"district": row.district or "Unknown", "cases": row.count} for row in res.all()]

    async def get_status_breakdown(self) -> list[dict]:
        """Fetch solved vs pending case counts."""
        stmt = (
            select(CaseMaster.case_status_id, func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .group_by(CaseMaster.case_status_id)
        )
        
        if self.authorized_districts is not None:
            stmt = stmt.join(CaseMaster.police_station).where(PoliceStation.district.in_(self.authorized_districts))

        res = await self.db.execute(stmt)
        
        status_map = {
            1: "Open",
            2: "Charge-Sheeted",
            3: "Closed",
            4: "Open"
        }
        
        breakdown = {
            "Open": 0,
            "Closed": 0,
            "Charge-Sheeted": 0
        }
        
        for row in res.all():
            lbl = status_map.get(row.case_status_id or 1, "Open")
            if lbl in breakdown:
                breakdown[lbl] += row.count
                
        return [{"name": k, "value": v} for k, v in breakdown.items() if v > 0]
