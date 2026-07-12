"""
app/db/init_db.py — database initialisation helpers.

Called once at application startup (via lifespan) to verify
the connection is alive. Table creation is handled exclusively
by Alembic migrations.
"""

import logging

from sqlalchemy import text

from app.db.session import engine

logger = logging.getLogger(__name__)


async def verify_db_connection() -> None:
    """
    Execute a trivial query to confirm the database is reachable.
    Raises on failure so the application fails fast at startup.
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified.")
