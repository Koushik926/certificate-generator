"""Integration tests for the certificate generation API."""
from __future__ import annotations

import asyncio
import time
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.models.base import Base
from app.main import app
from app.config import settings
from app.db.session import async_session_factory
from sqlalchemy.ext.asyncio import async_sessionmaker


@pytest.fixture(scope="module")
def test_engine():
    """Create a shared in-memory SQLite engine for the session. Creates tables."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async def _setup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    loop = asyncio.new_event_loop()
    loop.run_until_complete(_setup())
    yield engine
    loop.close()


@pytest.fixture
def client(test_engine):
    """Create a test client with DB override per test."""
    factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    app.dependency_overrides[async_session_factory] = lambda: factory()

    transport = ASGITransport(app=app)
    yield AsyncClient(transport=transport, base_url="http://test")
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    """Health check returns ok."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_generate_certificates(client: AsyncClient) -> None:
    """Submit a job and receive a job_id."""
    response = await client.post(
        "/api/v1/certificates/generate",
        json={
            "event_name": "Test Event",
            "issue_date": "2026-10-08",
            "template_style": "modern",
            "recipients": [
                {"name": "Alice Smith", "email": "alice@example.com"},
                {"name": "Bob Jones", "email": "bob@example.com"},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_invalid_date_format(client: AsyncClient) -> None:
    """Invalid payload returns 422."""
    response = await client.post(
        "/api/v1/certificates/generate",
        json={
            "event_name": "Test Event",
            "template_style": "modern",
            "recipients": [
                {"name": "", "email": "not-an-email"}
            ],
        },
    )
    assert response.status_code == 422