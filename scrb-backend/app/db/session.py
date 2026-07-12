"""
app/db/session.py — SQLAlchemy async engine + session factory.

Usage (FastAPI dependency injection):

    from app.db.session import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/")
    async def my_endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.config import settings

# ---------------------------------------------------------------------------
# Async Engine
# ---------------------------------------------------------------------------
# SQLite does not support pool_size or max_overflow.
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": (settings.app_env == "local"),
}
if not settings.database_url.startswith("sqlite"):
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_async_engine(
    settings.database_url,
    **engine_kwargs
)

# ---------------------------------------------------------------------------
# Async Session factory
# ---------------------------------------------------------------------------
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False,      # keep attributes accessible after commit
)


# ---------------------------------------------------------------------------
# FastAPI dependency (Async)
# ---------------------------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and guarantee it is closed after the request."""
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
