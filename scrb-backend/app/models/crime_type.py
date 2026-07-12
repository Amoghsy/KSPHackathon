from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.case import CaseMaster


class CrimeType(Base):
    __tablename__ = "crime_type"

    crime_type_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # TODO Confirm ER Schema

    # Relationships
    cases: Mapped[list["CaseMaster"]] = relationship(
        back_populates="crime_type",
        cascade="all, delete-orphan"
    )
