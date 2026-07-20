import datetime
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # Store UUID as String
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    device_name: Mapped[str] = mapped_column(String(255), default="Unknown Device")
    device_type: Mapped[str] = mapped_column(String(50), default="Unknown")
    browser: Mapped[str] = mapped_column(String(100), default="Unknown")
    operating_system: Mapped[str] = mapped_column(String(100), default="Unknown")
    ip_address: Mapped[str] = mapped_column(String(45), default="Unknown")
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    last_activity_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.datetime.utcnow
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoke_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
