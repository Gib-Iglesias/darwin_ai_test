"""
Pytest fixtures shared across all test modules.

Key fixtures:
  - `app_client`  – async TestClient with overridden DB and a valid JWT.
  - `db_session`  – in-memory SQLite session for fast unit tests.
  - `valid_token` – pre-signed JWT accepted by the app.
  - `sample_user` – a User row already inserted into the test DB.
"""

import json
import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Force test environment variables BEFORE importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("JWT_SECRET", "test-secret-for-ci")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "5")
os.environ.setdefault("ENVIRONMENT", "test")

from app.database import get_session                  # noqa: E402
from app.main import app                               # noqa: E402
from app.models import Base, User                     # noqa: E402

# ---------------------------------------------------------------------------
# In-memory SQLite engine (fast, isolated, no external DB needed)
# ---------------------------------------------------------------------------

test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_db():
    """Create tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Override the FastAPI DB dependency with our in-memory session
async def _override_get_session():
    async with TestSessionLocal() as session:
        yield session

app.dependency_overrides[get_session] = _override_get_session


# ---------------------------------------------------------------------------
# JWT helper
# ---------------------------------------------------------------------------

def _make_token(secret: str = "test-secret-for-ci", expired: bool = False) -> str:
    """Generate a signed JWT for use in test requests."""
    now = datetime.now(timezone.utc)
    exp = now - timedelta(minutes=1) if expired else now + timedelta(minutes=5)
    payload = {"service": "connector", "iat": now, "exp": exp}
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def valid_token() -> str:
    return _make_token()


@pytest.fixture
def expired_token() -> str:
    return _make_token(expired=True)


@pytest.fixture
def wrong_secret_token() -> str:
    return _make_token(secret="completely-wrong-secret")


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def app_client() -> AsyncClient:  # type: ignore[return]
    """Async HTTP client wired directly to the FastAPI app (no network needed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# ---------------------------------------------------------------------------
# Sample DB user
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def sample_user() -> User:  # type: ignore[return]
    """Insert a whitelisted user and return the ORM object."""
    async with TestSessionLocal() as session:
        user = User(telegram_id="123456789")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        yield user
