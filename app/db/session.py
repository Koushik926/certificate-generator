"""Async database session management."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.config import settings

_connect_args = (
    {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

_engine_kwargs: dict = {"echo": settings.DB_ECHO, "connect_args": _connect_args}
if "sqlite+aiosqlite:///:memory:" in settings.DATABASE_URL:
    _engine_kwargs["poolclass"] = StaticPool

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:  # type: ignore[no-untyped-def]
    """FastAPI dependency: yield a session, close it after the request."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (dev shortcut; prefer Alembic in production)."""
    from app.models.base import Base
    from app.models.models import Job, Recipient  # noqa: WPS433

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)