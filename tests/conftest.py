"""Shared test fixtures."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.session import async_session_factory
from app.models.base import Base
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    """Create a shared in-memory SQLite engine for the session. Creates tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(_setup())
    yield engine
    loop.close()


@pytest.fixture
def client(test_engine):
    """Test HTTP client with DB override per test."""
    factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    app.dependency_overrides[async_session_factory] = lambda: factory()
    from httpx import ASGITransport, AsyncClient
    yield AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
    app.dependency_overrides.clear()