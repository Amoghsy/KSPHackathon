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
