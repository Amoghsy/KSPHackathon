import datetime
from sqlalchemy import ForeignKey, String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DistrictAccessRequest(Base):
    __tablename__ = "district_access_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    requested_district: Mapped[str] = mapped_column(String(100), index=True)
    related_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("case_master.case_master_id", ondelete="SET NULL"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(Text)
    duration_hours: Mapped[int] = mapped_column()
    status: Mapped[str] = mapped_column(String(30), default="PENDING", index=True)
    # PENDING, APPROVED, REJECTED, MORE_INFO_REQUIRED, CANCELLED
    requested_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    review_comment: Mapped[str | None] = mapped_column(Text, nullable=True)


class TemporaryDistrictPermission(Base):
    __tablename__ = "temporary_district_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    district: Mapped[str] = mapped_column(String(100), index=True)
    access_request_id: Mapped[int] = mapped_column(ForeignKey("district_access_requests.id", ondelete="CASCADE"), index=True)
    approved_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    approved_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, index=True)
    related_case_id: Mapped[int | None] = mapped_column(ForeignKey("case_master.case_master_id", ondelete="SET NULL"), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
