import datetime
import logging
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import CaseMaster
from app.models.accused import AccusedMaster
from app.models.victim import VictimMaster
from app.models.police_station import PoliceStation
from app.models.crime_type import CrimeType
from app.models.financial_transaction import FinancialTransaction

logger = logging.getLogger(__name__)


class GraphRepository:
    """
    SQLAlchemy Repository layer for retrieving graph-related database entities.
    Centralises PostgreSQL access for Cases, Accused, Victims, and Transactions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_filtered_cases(
        self,
        district: str | None = None,
        crime_type: str | None = None,
        police_station: str | None = None,
        time_period: str | None = None,
    ) -> list[CaseMaster]:
        """
        Retrieves CaseMaster records filtered by district, crime type, station, and date range.
        Loads eager relationships to prevent lazy loading issues in async context.
        """
        stmt = select(CaseMaster).options(
            selectinload(CaseMaster.police_station),
            selectinload(CaseMaster.crime_type),
        )

        filters = []

        if district and district != "All":
            stmt = stmt.join(CaseMaster.police_station)
            filters.append(PoliceStation.district == district)

        if police_station and police_station != "All":
            # If not already joined
            if not district or district == "All":
                stmt = stmt.join(CaseMaster.police_station)
            filters.append(PoliceStation.name == police_station)

        if crime_type and crime_type != "All":
            stmt = stmt.join(CaseMaster.crime_type)
            filters.append(CrimeType.name == crime_type)

        if time_period and time_period != "All":
            try:
                days = int(time_period)
                cutoff = datetime.date.today() - datetime.timedelta(days=days)
                filters.append(CaseMaster.crime_registered_date >= cutoff)
            except ValueError:
                logger.warning("Invalid time_period format: %s", time_period)

        if filters:
            stmt = stmt.where(and_(*filters))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_cases_by_focus_id(self, focus_id: str) -> list[CaseMaster]:
        """
        Fetch cases related to a focus ID (Accused name/ID, Case number/ID, Location, etc.).
        """
        focus_clean = focus_id.strip()
        
        # 1. Check if Case ID (e.g. C12)
        if focus_clean.startswith("C") and focus_clean[1:].isdigit():
            case_id = int(focus_clean[1:])
            stmt = select(CaseMaster).where(CaseMaster.case_master_id == case_id).options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
            )
            result = await self.db.execute(stmt)
            c = result.scalar_one_or_none()
            return [c] if c else []
            
        # 2. Check if specific crime number / case number
        stmt = select(CaseMaster).where(
            or_(
                CaseMaster.crime_no == focus_clean,
                CaseMaster.case_no == focus_clean
            )
        ).options(
            selectinload(CaseMaster.police_station),
            selectinload(CaseMaster.crime_type),
        )
        result = await self.db.execute(stmt)
        cases = list(result.scalars().all())
        if cases:
            return cases

        # 3. Check if it matches an accused person (name, person_id, or format A_name)
        acc_search = focus_clean
        if acc_search.startswith("A_"):
            acc_search = acc_search[2:]
            
        # Select accused masters where person_id matches or name matches (normalized)
        from app.services.graph.graph_utils import normalize_name
        norm_search = normalize_name(acc_search)
        
        stmt = select(AccusedMaster).where(
            or_(
                AccusedMaster.person_id == focus_clean,
                AccusedMaster.accused_name.ilike(f"%{acc_search}%")
            )
        )
        result = await self.db.execute(stmt)
        accused_list = list(result.scalars().all())
        
        # fallback to normalized comparison if no direct matches
        if not accused_list and norm_search:
            stmt = select(AccusedMaster)
            result = await self.db.execute(stmt)
            all_acc = list(result.scalars().all())
            accused_list = [
                a for a in all_acc 
                if (a.person_id and normalize_name(a.person_id) == norm_search) 
                or normalize_name(a.accused_name) == norm_search
            ]
            
        if accused_list:
            case_ids = list({a.case_master_id for a in accused_list})
            stmt = select(CaseMaster).where(CaseMaster.case_master_id.in_(case_ids)).options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        # 4. Check if it matches a Police Station
        stmt = select(PoliceStation).where(PoliceStation.name.ilike(f"%{focus_clean}%"))
        result = await self.db.execute(stmt)
        stations = list(result.scalars().all())
        if stations:
            station_ids = [s.police_station_id for s in stations]
            stmt = select(CaseMaster).where(CaseMaster.police_station_id.in_(station_ids)).options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        # 5. Check if it matches a District
        # Join CaseMaster and PoliceStation to filter by district
        stmt = select(CaseMaster).join(CaseMaster.police_station).where(
            PoliceStation.district.ilike(f"%{focus_clean}%")
        ).options(
            selectinload(CaseMaster.police_station),
            selectinload(CaseMaster.crime_type),
        )
        result = await self.db.execute(stmt)
        cases = list(result.scalars().all())
        if cases:
            return cases

        # 6. Check if it matches a Crime Type
        stmt = select(CrimeType).where(CrimeType.name.ilike(f"%{focus_clean}%"))
        result = await self.db.execute(stmt)
        ct_types = list(result.scalars().all())
        if ct_types:
            ct_ids = [ct.crime_type_id for ct in ct_types]
            stmt = select(CaseMaster).where(CaseMaster.crime_type_id.in_(ct_ids)).options(
                selectinload(CaseMaster.police_station),
                selectinload(CaseMaster.crime_type),
            )
            result = await self.db.execute(stmt)
            return list(result.scalars().all())

        return []

    async def get_accused_for_cases(self, case_ids: list[int]) -> list[AccusedMaster]:
        """Fetch all accused associated with a list of Case IDs."""
        if not case_ids:
            return []
        stmt = select(AccusedMaster).where(AccusedMaster.case_master_id.in_(case_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_victims_for_cases(self, case_ids: list[int]) -> list[VictimMaster]:
        """Fetch all victims associated with a list of Case IDs."""
        if not case_ids:
            return []
        stmt = select(VictimMaster).where(VictimMaster.case_master_id.in_(case_ids))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_financial_transactions(
        self, case_ids: list[int] | None = None, accused_ids: list[int] | None = None
    ) -> list[FinancialTransaction]:
        """
        Fetch financial transactions connected to specific Case IDs or Accused IDs.
        If no IDs are passed, fetches all transactions for global financial analysis.
        """
        filters = []
        if case_ids:
            filters.append(FinancialTransaction.case_master_id.in_(case_ids))
        if accused_ids:
            filters.append(FinancialTransaction.accused_master_id.in_(accused_ids))

        if not filters:
            stmt = select(FinancialTransaction)
        else:
            stmt = select(FinancialTransaction).where(or_(*filters))

        stmt = stmt.options(
            selectinload(FinancialTransaction.accused),
            selectinload(FinancialTransaction.case),
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_police_stations(self) -> list[PoliceStation]:
        """Fetch all police stations."""
        stmt = select(PoliceStation)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_crime_types(self) -> list[CrimeType]:
        """Fetch all crime types."""
        stmt = select(CrimeType)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
