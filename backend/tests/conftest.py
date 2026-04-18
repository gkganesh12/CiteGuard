"""Shared test fixtures for CiteGuard backend tests."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.dependencies import AuthenticatedUser
from app.config import settings
from app.db.base import Base
from app.models.enums import UserRole

# Use test database
TEST_DATABASE_URL = settings.database_url.replace("/citeguard", "/citeguard_test")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
def test_firm_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def other_firm_id() -> uuid.UUID:
    """A different firm's ID for tenant isolation tests."""
    return uuid.uuid4()


@pytest.fixture
def test_user(test_firm_id: uuid.UUID) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        firm_id=test_firm_id,
        role=UserRole.ADMIN,
        email="test@example.com",
    )


@pytest.fixture
def test_reviewer(test_firm_id: uuid.UUID) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        firm_id=test_firm_id,
        role=UserRole.REVIEWER,
        email="reviewer@example.com",
    )


@pytest.fixture
def test_submitter(test_firm_id: uuid.UUID) -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id=uuid.uuid4(),
        firm_id=test_firm_id,
        role=UserRole.SUBMITTER,
        email="submitter@example.com",
    )
