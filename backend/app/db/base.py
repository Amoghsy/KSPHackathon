"""
app/db/base.py — SQLAlchemy declarative base.

Import `Base` in every model file so Alembic autogenerate
can discover all tables via Base.metadata.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Root base class for all ORM models."""

    pass
