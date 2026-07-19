import datetime
from sqlalchemy import ForeignKey, String, DateTime, Boolean, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserDistrictAssignment(Base):
    __tablename__ = "user_district_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    district: Mapped[str] = mapped_column(String(100), index=True)
    assigned_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    removed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    removed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        Index(
            "uq_active_user_district",
            "user_id",
            "district",
            unique=True,
            postgresql_where=text("is_active = TRUE"),
        ),
    )
