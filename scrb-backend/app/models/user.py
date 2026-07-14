from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"  # TODO Confirm ER Schema

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(100), unique=True, index=True
    )  # TODO Confirm ER Schema
    hashed_password: Mapped[str] = mapped_column(String(255))  # TODO Confirm ER Schema
    role: Mapped[str] = mapped_column(
        String(50), default="Investigator"
    )  # TODO Confirm ER Schema
    districts: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default=None
    )

