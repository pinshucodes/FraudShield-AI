"""
Database configuration and session management.

Uses async SQLAlchemy 2.0 with asyncpg for PostgreSQL
and aiosqlite for SQLite (development/testing).
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings


def _create_engine():
    """Create the async engine with appropriate config based on database type."""
    connect_args = {}
    kwargs = {"echo": settings.DEBUG}

    if settings.DATABASE_URL.startswith("sqlite"):
        # SQLite doesn't support pool_size/max_overflow
        connect_args = {"check_same_thread": False}
        kwargs["connect_args"] = connect_args
    else:
        # PostgreSQL supports connection pooling
        kwargs["pool_size"] = settings.DATABASE_POOL_SIZE
        kwargs["max_overflow"] = settings.DATABASE_MAX_OVERFLOW
        kwargs["pool_pre_ping"] = True

    return create_async_engine(settings.DATABASE_URL, **kwargs)


engine = _create_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

