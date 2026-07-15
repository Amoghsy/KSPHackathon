import logging

from sqlalchemy import text, select

from app.db.session import engine, SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.core.rbac import UserRole

logger = logging.getLogger(__name__)


async def verify_db_connection() -> None:
    """
    Execute a trivial query to confirm the database is reachable.
    Raises on failure so the application fails fast at startup.
    """
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection verified.")


async def seed_default_admin() -> None:
    """
    Check if a default administrator user exists.
    If not, create one with username 'admin' and password 'admin123'.
    """
    async with SessionLocal() as db:
        try:
            stmt = select(User).where(User.username == "admin")
            result = await db.execute(stmt)
            admin_user = result.scalar_one_or_none()

            if not admin_user:
                logger.info("Default administrator 'admin' not found. Creating one...")
                hashed_pw = get_password_hash("admin123")
                new_admin = User(
                    username="admin",
                    hashed_password=hashed_pw,
                    role=UserRole.ADMIN.value,
                )
                db.add(new_admin)
                await db.commit()
                logger.info("Default administrator 'admin' successfully created.")
            else:
                logger.info("Default administrator 'admin' already exists.")
        except Exception as exc:
            logger.warning("Could not seed default admin user: %s", exc)
            await db.rollback()
