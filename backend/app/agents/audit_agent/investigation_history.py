import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.investigation_history import InvestigationHistory


class InvestigationHistoryService:
    """
    Service to track and retrieve user-initiated investigations.
    Supports timeline tracing and reopening previous sessions.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_entry(
        self,
        user_id: int,
        name: str,
        entity_type: str,
        entity_id: str
    ) -> InvestigationHistory:
        entry = InvestigationHistory(
            user_id=user_id,
            investigation_name=name,
            entity_type=entity_type,
            entity_id=entity_id,
            timestamp=datetime.datetime.utcnow()
        )
        self.db.add(entry)
        await self.db.commit()
        return entry

    async def get_history(self, user_id: int, limit: int = 30) -> list[dict]:
        stmt = (
            select(InvestigationHistory)
            .where(InvestigationHistory.user_id == user_id)
            .order_by(InvestigationHistory.timestamp.desc())
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": r.id,
                "name": r.investigation_name,
                "type": r.entity_type,
                "entity_id": r.entity_id,
                "timestamp": r.timestamp.isoformat() + "Z"
            }
            for r in rows
        ]
