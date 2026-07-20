import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.accused import AccusedMaster
    from app.models.crime_type import CrimeType
    from app.models.financial_transaction import FinancialTransaction
    from app.models.police_station import PoliceStation
    from app.models.victim import VictimMaster
    from app.models.complainant import ComplainantDetails


class CaseMaster(Base):
    __tablename__ = "case_master"

    case_master_id: Mapped[int] = mapped_column(primary_key=True)
    crime_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    case_no: Mapped[str | None] = mapped_column(String(50), index=True)
    crime_registered_date: Mapped[datetime.date] = mapped_column(Date)

    # Foreign Keys
    police_station_id: Mapped[int | None] = mapped_column(
        ForeignKey("police_station.police_station_id", ondelete="SET NULL"), index=True
    )
    crime_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("crime_type.crime_type_id", ondelete="SET NULL"), index=True
    )  # TODO Confirm ER Schema

    # Non-ForeignKey fields (TODO Confirm ER Schema for lookup values)
    police_person_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    case_category_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    gravity_offence_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    crime_major_head_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    crime_minor_head_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    case_status_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema
    court_id: Mapped[int | None] = mapped_column()  # TODO Confirm ER Schema

    # DateTimes and Numeric fields
    incident_from_date: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    incident_to_date: Mapped[datetime.datetime | None] = mapped_column(DateTime)
    info_received_ps_date: Mapped[datetime.datetime | None] = mapped_column(DateTime)

    latitude: Mapped[Decimal | None] = mapped_column(Numeric(precision=9, scale=6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(precision=9, scale=6))
    brief_facts: Mapped[str | None] = mapped_column(Text)

    # Relationships
    police_station: Mapped["PoliceStation"] = relationship(back_populates="cases")
    crime_type: Mapped["CrimeType"] = relationship(back_populates="cases")
    accused: Mapped[list["AccusedMaster"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    victims: Mapped[list["VictimMaster"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    financial_transactions: Mapped[list["FinancialTransaction"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
    complainants: Mapped[list["ComplainantDetails"]] = relationship(
        back_populates="case", cascade="all, delete-orphan"
    )
