"""
Shared fixtures for integration tests.

The test database URL is read from the DATABASE_URL env var (defaulting to a
local test database). All required settings env vars are set before any app
module is imported so pydantic-settings picks them up correctly.
"""
import os
from contextlib import asynccontextmanager
from unittest.mock import patch

# Set all required env vars BEFORE importing any app module.
# SMTP_HOST is intentionally left empty so email_service logs codes instead of
# trying to connect to a real SMTP server.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/barbertime_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci-only-not-used-in-production")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")
os.environ.setdefault("STRIPE_PRICE_ID", "price_dummy")
os.environ.setdefault("SMTP_HOST", "")

# /app/uploads must exist for FastAPI's StaticFiles mount (happens at import time).
os.makedirs("/app/uploads", exist_ok=True)

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

# Replace the app lifespan with a no-op so we don't start the background
# cleanup loop or try to mkdir /app/uploads a second time during tests.
@asynccontextmanager
async def _noop_lifespan(app):
    yield

import app.main as _main_module
_main_module.app.router.lifespan_context = _noop_lifespan

from app.main import app
from app.core.database import Base, get_db
# Import all models so their tables are registered with Base.metadata.
from app.models.shop import Shop
from app.models.employee import Employee
from app.models.reservation import Reservation, ReservationStatus
from app.models.flash_discount import FlashDiscount
from app.models.queue_history import QueueHistory
from app.models.verification_code import VerificationCode, VerificationPurpose

TEST_DB_URL = os.environ["DATABASE_URL"]
_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSession = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def _override_get_db():
    async with _TestSession() as session:
        yield session


app.dependency_overrides[get_db] = _override_get_db


# ── database lifecycle ────────────────────────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
async def create_tables():
    """Create all tables once per test session, drop them afterwards."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def clean_tables(create_tables):
    """Truncate every table after each test to keep tests isolated."""
    yield
    async with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


# ── HTTP client ───────────────────────────────────────────────────────────────

@pytest.fixture
async def client(tmp_path):
    """HTTP client wired to the FastAPI test app with uploads redirected to tmp_path."""
    import app.core.upload as _upload
    with patch.object(_upload, "UPLOAD_DIR", str(tmp_path)):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as c:
            yield c


# ── auth helpers ──────────────────────────────────────────────────────────────

@pytest.fixture
async def register(client):
    """Return a helper that registers a shop and returns its JWT token."""
    async def _register(email="barber@example.com", password="password123", name="Test Shop"):
        resp = await client.post("/api/v1/auth/register", json={
            "email": email,
            "password": password,
            "name": name,
        })
        assert resp.status_code == 201, resp.text
        return resp.json()["access_token"]
    return _register


@pytest.fixture
async def token(register):
    return await register()


@pytest.fixture
async def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def subscribed_headers(auth_headers):
    """Set the shop's subscription to active and return auth headers."""
    async with _TestSession() as db:
        result = await db.execute(select(Shop))
        shop = result.scalars().first()
        shop.subscription_status = "active"
        await db.commit()
    return auth_headers


# ── DB query helpers used across test files ───────────────────────────────────

async def get_verification_code(email: str, purpose: VerificationPurpose) -> str:
    """Fetch the latest unused verification code for the given email+purpose."""
    async with _TestSession() as db:
        result = await db.execute(
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.purpose == purpose,
                VerificationCode.used == False,  # noqa: E712
            )
            .order_by(VerificationCode.id.desc())
        )
        code = result.scalars().first()
        assert code is not None, f"No verification code found for {email}"
        return code.code
