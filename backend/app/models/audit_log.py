import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    api: Mapped[str | None] = mapped_column(String(255), nullable=True)
    response_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    request_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # New security audit columns
    action: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    target_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supervisor_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    district_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    case_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)

