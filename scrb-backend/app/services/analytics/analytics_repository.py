import datetime
from decimal import Decimal
from sqlalchemy import func, select, and_, extract, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.models.accused import AccusedMaster


class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _apply_filters(self, stmt, district: str | None = None, crime_type: str | None = None,
                       police_station: str | None = None, start_date: datetime.date | None = None,
                       end_date: datetime.date | None = None):
        """Helper to apply standard query filters to SQLAlchemy statements."""
        conditions = []
        if district and district != "All":
            stmt = stmt.join(CaseMaster.police_station)
            conditions.append(PoliceStation.district == district)
        elif police_station and police_station != "All":
            stmt = stmt.join(CaseMaster.police_station)
            conditions.append(PoliceStation.name == police_station)

        if crime_type and crime_type != "All":
            # Avoid duplicate joins
            stmt = stmt.join(CaseMaster.crime_type)
            conditions.append(CrimeType.name == crime_type)

        if start_date:
            conditions.append(CaseMaster.crime_registered_date >= start_date)
        if end_date:
            conditions.append(CaseMaster.crime_registered_date <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))
        return stmt

    async def get_monthly_trends(self, district: str | None = None, crime_type: str | None = None,
                                  police_station: str | None = None, start_date: datetime.date | None = None,
                                  end_date: datetime.date | None = None) -> list[dict]:
        """Fetch monthly case counts for time series trend."""
        # Use date_trunc for PostgreSQL monthly aggregation
        month_trunc = func.date_trunc('month', CaseMaster.crime_registered_date)
        stmt = (
            select(month_trunc.label('month_date'), func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .group_by(month_trunc)
            .order_by(month_trunc)
        )
        stmt = self._apply_filters(stmt, district, crime_type, police_station, start_date, end_date)
        res = await self.db.execute(stmt)
        results = []
        for row in res.all():
            dt = row.month_date
            # dt is a datetime object or date
            results.append({
                "month": dt.strftime("%b %Y") if dt else "Unknown",
                "count": row.count,
                "raw_date": dt
            })
        return sorted(results, key=lambda x: x["raw_date"])

    async def get_daily_trends(self, district: str | None = None, crime_type: str | None = None,
                                 police_station: str | None = None, start_date: datetime.date | None = None,
                                 end_date: datetime.date | None = None) -> list[dict]:
        """Fetch daily case counts."""
        stmt = (
            select(CaseMaster.crime_registered_date.label('day_date'), func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .group_by(CaseMaster.crime_registered_date)
            .order_by(CaseMaster.crime_registered_date)
        )
        stmt = self._apply_filters(stmt, district, crime_type, police_station, start_date, end_date)
        res = await self.db.execute(stmt)
        return [
            {
                "date": row.day_date.strftime("%Y-%m-%d") if row.day_date else "Unknown",
                "count": row.count
            }
            for row in res.all()
        ]

    async def get_district_counts(self, limit: int = 10) -> list[dict]:
        """Fetch total case count per district."""
        stmt = (
            select(PoliceStation.district, func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .join(CaseMaster.police_station)
            .group_by(PoliceStation.district)
            .order_by(func.count(CaseMaster.case_master_id).desc())
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return [{"district": row.district or "Unknown", "cases": row.count} for row in res.all()]

    async def get_police_station_counts(self, district: str | None = None, limit: int = 10) -> list[dict]:
        """Fetch top police stations by case count."""
        stmt = (
            select(PoliceStation.name, PoliceStation.district, func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .join(CaseMaster.police_station)
            .group_by(PoliceStation.name, PoliceStation.district)
            .order_by(func.count(CaseMaster.case_master_id).desc())
        )
        if district and district != "All":
            stmt = stmt.where(PoliceStation.district == district)
        stmt = stmt.limit(limit)
        res = await self.db.execute(stmt)
        return [{"station": row.name, "district": row.district, "cases": row.count} for row in res.all()]

    async def get_crime_type_counts(self, district: str | None = None, limit: int = 15) -> list[dict]:
        """Fetch case counts by crime type."""
        stmt = (
            select(CrimeType.name, func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .join(CaseMaster.crime_type)
            .group_by(CrimeType.name)
            .order_by(func.count(CaseMaster.case_master_id).desc())
        )
        if district and district != "All":
            stmt = stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
        stmt = stmt.limit(limit)
        res = await self.db.execute(stmt)
        return [{"crime_type": row.name, "cases": row.count} for row in res.all()]

    async def get_status_breakdown(self, district: str | None = None) -> list[dict]:
        """Fetch solved vs pending status counts."""
        # 1: Under Investigation (Pending)
        # 2: Charge Sheeted (Solved)
        # 3: Closed (Solved)
        # 4: Undetected (Pending)
        stmt = (
            select(CaseMaster.case_status_id, func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .group_by(CaseMaster.case_status_id)
        )
        if district and district != "All":
            stmt = stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
        res = await self.db.execute(stmt)
        
        status_map = {
            1: "Under Investigation",
            2: "Charge Sheeted",
            3: "Closed",
            4: "Undetected"
        }
        
        breakdown = {
            "Open": 0,
            "Closed": 0,
            "Charge-Sheeted": 0,
            "Undetected": 0
        }
        
        for row in res.all():
            lbl = status_map.get(row.case_status_id or 1, "Under Investigation")
            if lbl == "Under Investigation":
                breakdown["Open"] += row.count
            elif lbl == "Closed":
                breakdown["Closed"] += row.count
            elif lbl == "Charge Sheeted":
                breakdown["Charge-Sheeted"] += row.count
            else:
                breakdown["Undetected"] += row.count
                
        return [{"name": k, "value": v} for k, v in breakdown.items() if v > 0]

    async def get_crime_coordinates(self, district: str | None = None, crime_type: str | None = None,
                                     police_station: str | None = None, start_date: datetime.date | None = None,
                                     end_date: datetime.date | None = None) -> list[dict]:
        """Fetch list of coordinates and metadata for spatial clustering."""
        stmt = (
            select(
                CaseMaster.latitude,
                CaseMaster.longitude,
                CrimeType.name.label('crime_name'),
                CaseMaster.gravity_offence_id,
                PoliceStation.district
            )
            .select_from(CaseMaster)
            .join(CaseMaster.crime_type)
            .join(CaseMaster.police_station)
            .where(CaseMaster.latitude.isnot(None))
            .where(CaseMaster.longitude.isnot(None))
        )
        stmt = self._apply_filters(stmt, district, crime_type, police_station, start_date, end_date)
        res = await self.db.execute(stmt)
        return [
            {
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "crime_type": row.crime_name,
                "gravity": row.gravity_offence_id or 2,
                "district": row.district
            }
            for row in res.all()
        ]

    async def get_temporal_distribution(self, district: str | None = None, crime_type: str | None = None) -> dict:
        """Fetch hour-of-day, day-of-week, and weekend vs working day distributions."""
        # Hour of day distribution
        hour_stmt = (
            select(extract('hour', CaseMaster.incident_from_date).label('hour'), func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .where(CaseMaster.incident_from_date.isnot(None))
            .group_by(extract('hour', CaseMaster.incident_from_date))
            .order_by(extract('hour', CaseMaster.incident_from_date))
        )
        if district and district != "All":
            hour_stmt = hour_stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
        if crime_type and crime_type != "All":
            hour_stmt = hour_stmt.join(CaseMaster.crime_type).where(CrimeType.name == crime_type)
            
        hour_res = await self.db.execute(hour_stmt)
        hour_counts = {int(row.hour): row.count for row in hour_res.all() if row.hour is not None}
        
        # Day of week distribution (DOW: 0 is Sunday in postgres extract)
        dow_stmt = (
            select(extract('dow', CaseMaster.crime_registered_date).label('dow'), func.count(CaseMaster.case_master_id).label('count'))
            .select_from(CaseMaster)
            .group_by(extract('dow', CaseMaster.crime_registered_date))
            .order_by(extract('dow', CaseMaster.crime_registered_date))
        )
        if district and district != "All":
            dow_stmt = dow_stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
        if crime_type and crime_type != "All":
            dow_stmt = dow_stmt.join(CaseMaster.crime_type).where(CrimeType.name == crime_type)
            
        dow_res = await self.db.execute(dow_stmt)
        dow_counts = {int(row.dow): row.count for row in dow_res.all() if row.dow is not None}
        
        # Build response formats
        hours = [{"hour": h, "count": hour_counts.get(h, 0)} for h in range(24)]
        
        dow_names = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
        days = [{"day": dow_names[d], "count": dow_counts.get(d, 0)} for d in range(7)]
        
        weekend_count = dow_counts.get(0, 0) + dow_counts.get(6, 0)
        weekday_count = sum(dow_counts.get(d, 0) for d in range(1, 6))
        
        return {
            "byHour": hours,
            "byDay": days,
            "workingDays": weekday_count,
            "weekends": weekend_count
        }

    async def get_accused_demographics(self, district: str | None = None) -> dict:
        """Fetch accused age and gender demographics."""
        # Age bands
        age_case = case(
            (AccusedMaster.age_year < 18, "Under 18"),
            (and_(AccusedMaster.age_year >= 18, AccusedMaster.age_year <= 25), "18-25"),
            (and_(AccusedMaster.age_year >= 26, AccusedMaster.age_year <= 35), "26-35"),
            (and_(AccusedMaster.age_year >= 36, AccusedMaster.age_year <= 45), "36-45"),
            (and_(AccusedMaster.age_year >= 46, AccusedMaster.age_year <= 60), "46-60"),
            (AccusedMaster.age_year > 60, "Over 60"),
            else_="Unknown"
        )
        
        age_stmt = (
            select(age_case.label('age_band'), func.count(AccusedMaster.accused_master_id).label('count'))
            .select_from(AccusedMaster)
            .group_by(age_case)
        )
        if district and district != "All":
            age_stmt = age_stmt.join(AccusedMaster.case).join(CaseMaster.police_station).where(PoliceStation.district == district)
            
        age_res = await self.db.execute(age_stmt)
        by_age = [{"band": row.age_band, "count": row.count} for row in age_res.all()]
        
        # Gender
        gender_case = case(
            (AccusedMaster.gender_id == 1, "Male"),
            (AccusedMaster.gender_id == 2, "Female"),
            else_="Other"
        )
        gender_stmt = (
            select(gender_case.label('gender'), func.count(AccusedMaster.accused_master_id).label('count'))
            .select_from(AccusedMaster)
            .group_by(gender_case)
        )
        if district and district != "All":
            gender_stmt = gender_stmt.join(AccusedMaster.case).join(CaseMaster.police_station).where(PoliceStation.district == district)
            
        gender_res = await self.db.execute(gender_stmt)
        by_gender = [{"gender": row.gender, "count": row.count} for row in gender_res.all()]
        
        return {
            "byAge": by_age,
            "byGender": by_gender
        }

    async def get_total_kpis(self, district: str | None = None) -> dict:
        """Fetch counts for dashboard KPIs."""
        cases_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster)
        accused_stmt = select(func.count(AccusedMaster.accused_master_id)).select_from(AccusedMaster)
        
        open_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster).where(CaseMaster.case_status_id == 1)
        closed_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster).where(CaseMaster.case_status_id == 3)
        cs_stmt = select(func.count(CaseMaster.case_master_id)).select_from(CaseMaster).where(CaseMaster.case_status_id == 2)
        
        if district and district != "All":
            cases_stmt = cases_stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
            accused_stmt = accused_stmt.join(AccusedMaster.case).join(CaseMaster.police_station).where(PoliceStation.district == district)
            open_stmt = open_stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
            closed_stmt = closed_stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
            cs_stmt = cs_stmt.join(CaseMaster.police_station).where(PoliceStation.district == district)
            
        cases_res = await self.db.execute(cases_stmt)
        accused_res = await self.db.execute(accused_stmt)
        open_res = await self.db.execute(open_stmt)
        closed_res = await self.db.execute(closed_stmt)
        cs_res = await self.db.execute(cs_stmt)
        
        # Districts active count
        dist_stmt = select(func.count(func.distinct(PoliceStation.district))).select_from(PoliceStation)
        dist_res = await self.db.execute(dist_stmt)
        
        return {
            "total_cases": cases_res.scalar() or 0,
            "total_accused": accused_res.scalar() or 0,
            "open_cases": open_res.scalar() or 0,
            "closed_cases": closed_res.scalar() or 0,
            "charge_sheeted": cs_res.scalar() or 0,
            "districts_active": dist_res.scalar() or 0,
        }
