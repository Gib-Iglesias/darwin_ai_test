"""
Async database engine and session factory.

We use SQLAlchemy 2.x with the asyncpg driver for non-blocking I/O.
The module exposes:
  - `init_db()` / `close_db()` – called by FastAPI's lifespan hook.
  - `get_session()` – FastAPI dependency that yields a scoped async session.
"""

import os

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.environ["DATABASE_URL"]  # Fail fast if not set

engine = create_async_engine(
    DATABASE_URL,
    # Pool size tuned for a small service; adjust via env vars if needed.
    pool_size=5,
    max_overflow=10,
    # Echo SQL in development only – avoids log noise in production/test.
    echo=os.getenv("ENVIRONMENT", "production") == "development",
    future=True,
)

# Session factory – `expire_on_commit=False` prevents lazy-load errors after
# a commit when we still need to read the committed object's attributes.
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ---------------------------------------------------------------------------
# Lifecycle helpers (called from main.py lifespan)
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """
    Create all tables that don't exist yet.

    In production you'd use Alembic migrations instead, but for this test
    `create_all` is sufficient and keeps setup simple.
    """
    import sqlalchemy.exc
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except sqlalchemy.exc.IntegrityError:
        # If multiple uvicorn workers try to create the tables concurrently,
        # we can safely ignore the IntegrityError.
        pass
    except sqlalchemy.exc.ProgrammingError:
        # Also handles concurrent index/sequence creation conflicts.
        pass


async def close_db() -> None:
    """Dispose the connection pool on shutdown to free DB connections."""
    await engine.dispose()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_session() -> AsyncSession:  # type: ignore[return]
    """
    Yields an `AsyncSession` scoped to a single HTTP request.

    Usage in a route:
        async def my_route(db: AsyncSession = Depends(get_session)): ...
    """
    async with AsyncSessionLocal() as session:
        yield session
