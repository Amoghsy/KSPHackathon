from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.accused import AccusedMaster
from app.models.case import CaseMaster
from app.models.police_station import PoliceStation
from app.models.financial_transaction import FinancialTransaction
from app.models.victim import VictimMaster

class RiskRepository:
    """
    SQLAlchemy Repository layer for retrieving risk-related database entities
    under ABAC containment.
    """

    def __init__(self, db: AsyncSession, authorized_districts: list[str] | None = None):
        self.db = db
        self.authorized_districts = authorized_districts

    async def get_authorized_offenders_data(
        self, district: str | None = None
    ) -> list[AccusedMaster]:
        """
        Fetch AccusedMaster records with case history and transactions,
        restricted by authorized districts.
        """
        # Join case and police station to filter on district
        stmt = (
            select(AccusedMaster)
            .join(AccusedMaster.case)
            .join(CaseMaster.police_station)
            .options(
                selectinload(AccusedMaster.case).selectinload(CaseMaster.police_station),
                selectinload(AccusedMaster.case).selectinload(CaseMaster.crime_type),
                selectinload(AccusedMaster.financial_transactions),
                selectinload(AccusedMaster.case).selectinload(CaseMaster.accused)  # For co-accused associates
            )
        )

        conditions = []
        if district and district != "All":
            conditions.append(PoliceStation.district == district)
        
        if self.authorized_districts is not None:
            conditions.append(PoliceStation.district.in_(self.authorized_districts))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_authorized_cases_with_relations(
        self, district: str | None = None
    ) -> tuple[list[CaseMaster], list[AccusedMaster], list[VictimMaster], list[FinancialTransaction]]:
        """
        Fetch cases, accused, victims, and financial transactions within the authorized district scope.
        Used to build a localized district NetworkX graph.
        """
        stmt = select(CaseMaster).options(
            selectinload(CaseMaster.police_station),
            selectinload(CaseMaster.crime_type),
        )

        conditions = []
        has_joined_ps = False

        if district and district != "All":
            stmt = stmt.join(CaseMaster.police_station)
            conditions.append(PoliceStation.district == district)
            has_joined_ps = True

        if self.authorized_districts is not None:
            if not has_joined_ps:
                stmt = stmt.join(CaseMaster.police_station)
                has_joined_ps = True
            conditions.append(PoliceStation.district.in_(self.authorized_districts))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        res_cases = await self.db.execute(stmt)
        cases = list(res_cases.scalars().all())
        case_ids = [c.case_master_id for c in cases]

        if not case_ids:
            return [], [], [], []

        # Load child records
        stmt_acc = select(AccusedMaster).where(AccusedMaster.case_master_id.in_(case_ids))
        res_acc = await self.db.execute(stmt_acc)
        accused = list(res_acc.scalars().all())

        stmt_vic = select(VictimMaster).where(VictimMaster.case_master_id.in_(case_ids))
        res_vic = await self.db.execute(stmt_vic)
        victims = list(res_vic.scalars().all())

        accused_ids = [a.accused_master_id for a in accused]
        stmt_tx = select(FinancialTransaction).where(
            or_(
                FinancialTransaction.case_master_id.in_(case_ids),
                FinancialTransaction.accused_master_id.in_(accused_ids)
            )
        ).options(
            selectinload(FinancialTransaction.accused),
            selectinload(FinancialTransaction.case)
        )
        res_tx = await self.db.execute(stmt_tx)
        transactions = list(res_tx.scalars().all())

        return cases, accused, victims, transactions
