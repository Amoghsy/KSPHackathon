from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case import CaseMaster
    from app.models.financial_transaction import FinancialTransaction


class AccusedMaster(Base):
    __tablename__ = "accused_master"

    accused_master_id: Mapped[int] = mapped_column(primary_key=True)
    case_master_id: Mapped[int] = mapped_column(
        ForeignKey("case_master.case_master_id", ondelete="CASCADE"), index=True
    )
    accused_name: Mapped[str] = mapped_column(String(255), index=True)

    # Optional fields (TODO Confirm ER Schema)
    age_year: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    gender_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    person_id: Mapped[str | None] = mapped_column(
        String(50), index=True
    )  # TODO Confirm ER Schema

    # Relationships
    case: Mapped["CaseMaster"] = relationship(back_populates="accused")
    financial_transactions: Mapped[list["FinancialTransaction"]] = relationship(
        back_populates="accused", cascade="all, delete-orphan"
    )
