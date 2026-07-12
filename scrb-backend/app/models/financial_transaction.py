import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.accused import AccusedMaster
    from app.models.case import CaseMaster


class FinancialTransaction(Base):
    __tablename__ = "financial_transaction"

    financial_transaction_id: Mapped[int] = mapped_column(primary_key=True)

    # Account info
    source_account: Mapped[str] = mapped_column(String(100), index=True)
    destination_account: Mapped[str] = mapped_column(String(100), index=True)
    bank_name: Mapped[str | None] = mapped_column(String(100))  # TODO Confirm ER Schema

    # Transaction details
    amount: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2))
    transaction_date: Mapped[datetime.datetime] = mapped_column(DateTime)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str | None] = mapped_column(String(255))  # TODO Confirm ER Schema

    # Linked entities
    case_master_id: Mapped[int | None] = mapped_column(
        ForeignKey("case_master.case_master_id", ondelete="SET NULL"), index=True
    )
    accused_master_id: Mapped[int | None] = mapped_column(
        ForeignKey("accused_master.accused_master_id", ondelete="SET NULL"), index=True
    )

    # Relationships
    case: Mapped["CaseMaster | None"] = relationship(
        back_populates="financial_transactions"
    )
    accused: Mapped["AccusedMaster | None"] = relationship(
        back_populates="financial_transactions"
    )
