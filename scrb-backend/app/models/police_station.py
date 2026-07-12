from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case import CaseMaster


class PoliceStation(Base):
    __tablename__ = "police_station"

    police_station_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)  # TODO Confirm ER Schema
    district: Mapped[str | None] = mapped_column(
        String(100), index=True
    )  # TODO Confirm ER Schema

    # Relationships
    cases: Mapped[list["CaseMaster"]] = relationship(
        back_populates="police_station", cascade="all, delete-orphan"
    )
