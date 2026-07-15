from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case import CaseMaster


class VictimMaster(Base):
    __tablename__ = "victim_master"

    victim_master_id: Mapped[int] = mapped_column(primary_key=True)
    case_master_id: Mapped[int] = mapped_column(
        ForeignKey("case_master.case_master_id", ondelete="CASCADE"), index=True
    )
    victim_name: Mapped[str] = mapped_column(String(255), index=True)

    # Optional fields (TODO Confirm ER Schema)
    age_year: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    gender_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    victim_police: Mapped[bool | None] = mapped_column(
        Boolean, default=False
    )  # TODO Confirm ER Schema

    # Relationships
    case: Mapped["CaseMaster"] = relationship(back_populates="victims")
