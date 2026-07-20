from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case import CaseMaster


class CasteMaster(Base):
    __tablename__ = "caste_master"

    caste_master_id: Mapped[int] = mapped_column(primary_key=True)
    caste_master_name: Mapped[str] = mapped_column(String(255), index=True)

    complainants: Mapped[list["ComplainantDetails"]] = relationship(
        back_populates="caste"
    )


class ReligionMaster(Base):
    __tablename__ = "religion_master"

    religion_id: Mapped[int] = mapped_column(primary_key=True)
    religion_name: Mapped[str] = mapped_column(String(255), index=True)

    complainants: Mapped[list["ComplainantDetails"]] = relationship(
        back_populates="religion"
    )


class OccupationMaster(Base):
    __tablename__ = "occupation_master"

    occupation_id: Mapped[int] = mapped_column(primary_key=True)
    occupation_name: Mapped[str] = mapped_column(String(255), index=True)

    complainants: Mapped[list["ComplainantDetails"]] = relationship(
        back_populates="occupation"
    )


class ComplainantDetails(Base):
    __tablename__ = "complainant_details"

    complainant_id: Mapped[int] = mapped_column(primary_key=True)
    case_master_id: Mapped[int] = mapped_column(
        ForeignKey("case_master.case_master_id", ondelete="CASCADE"), index=True
    )
    complainant_name: Mapped[str] = mapped_column(String(255), index=True)
    age_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Foreign Keys
    occupation_id: Mapped[int | None] = mapped_column(
        ForeignKey("occupation_master.occupation_id", ondelete="SET NULL"), nullable=True, index=True
    )
    religion_id: Mapped[int | None] = mapped_column(
        ForeignKey("religion_master.religion_id", ondelete="SET NULL"), nullable=True, index=True
    )
    caste_id: Mapped[int | None] = mapped_column(
        ForeignKey("caste_master.caste_master_id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    case: Mapped["CaseMaster"] = relationship(back_populates="complainants")
    occupation: Mapped[OccupationMaster | None] = relationship(back_populates="complainants")
    religion: Mapped[ReligionMaster | None] = relationship(back_populates="complainants")
    caste: Mapped[CasteMaster | None] = relationship(back_populates="complainants")
