"""
alembic/env.py — Alembic migration environment.

Key points:
- Reads DATABASE_URL from app.config.settings (never hard-coded).
- Imports Base from app.db.base so autogenerate discovers all models.
- Supports both online and offline migration modes.
"""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# ---------------------------------------------------------------------------
# Make sure the project root is on sys.path so `app.*` imports resolve
# when Alembic is invoked from the repo root.
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import all models so their tables are registered on Base.metadata.
# Add new model imports here as they are created (Day 2+).
import app.models  # noqa: F401, E402
# ---------------------------------------------------------------------------
# Pull in application settings and the declarative base.
# ---------------------------------------------------------------------------
from app.config import settings  # noqa: E402
from app.db.base import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Alembic Config object (gives access to values within alembic.ini).
# ---------------------------------------------------------------------------
config = context.config

# Override the sqlalchemy.url from settings — credentials stay in .env.
config.set_main_option("sqlalchemy.url", settings.database_url)

# Set up Python logging as configured in alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations  (no live DB connection required)
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    """
    Run migrations without a real database connection.
    Useful for generating SQL scripts to review before applying.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations  (connects to the database and applies changes)
# ---------------------------------------------------------------------------
def run_migrations_online() -> None:
    """Run migrations against a live database connection."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
