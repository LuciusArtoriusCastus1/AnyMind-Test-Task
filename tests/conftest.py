"""
Pytest Configuration and Fixtures

This module provides shared fixtures for all tests:
- Database setup with PostgreSQL for full compatibility
- Test client for HTTP/GraphQL requests
- Sample data generators

Using PostgreSQL for tests to ensure full compatibility with production.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.database import Base
from app.main import app
from app.models.payment import Payment, PaymentMethod

settings = get_settings()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """
    Create a test database engine.

    Uses PostgreSQL for full compatibility with production.
    Creates fresh tables for each test.
    """
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Provides an isolated session for each test that is rolled back
    after the test completes.
    """
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def test_client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client for HTTP requests.

    This client can be used to test the FastAPI endpoints
    including the GraphQL endpoint.
    """
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    with patch("app.main.AsyncSessionLocal", TestSessionLocal):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest_asyncio.fixture
async def sample_payments(test_engine) -> list[Payment]:
    """
    Create sample payment records for testing.

    Returns a list of payments with various methods and amounts
    for use in sales report tests.
    """
    TestSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    payments = [
        Payment(
            customer_id="customer1",
            price=Decimal("100.00"),
            price_modifier=Decimal("0.95"),
            final_price=Decimal("95.00"),
            points=3,
            payment_method=PaymentMethod.VISA.value,
            additional_item={"last4": "1234"},
            datetime=datetime(2022, 9, 1, 0, 30, tzinfo=UTC),
        ),
        Payment(
            customer_id="customer2",
            price=Decimal("200.00"),
            price_modifier=Decimal("1.0"),
            final_price=Decimal("200.00"),
            points=10,
            payment_method=PaymentMethod.CASH.value,
            additional_item={},
            datetime=datetime(2022, 9, 1, 0, 45, tzinfo=UTC),
        ),
        Payment(
            customer_id="customer1",
            price=Decimal("150.00"),
            price_modifier=Decimal("1.0"),
            final_price=Decimal("150.00"),
            points=7,
            payment_method=PaymentMethod.CASH_ON_DELIVERY.value,
            additional_item={"courier": "YAMATO"},
            datetime=datetime(2022, 9, 1, 1, 15, tzinfo=UTC),
        ),
        Payment(
            customer_id="customer3",
            price=Decimal("500.00"),
            price_modifier=Decimal("0.98"),
            final_price=Decimal("490.00"),
            points=10,
            payment_method=PaymentMethod.AMEX.value,
            additional_item={"last4": "5678"},
            datetime=datetime(2022, 9, 1, 2, 0, tzinfo=UTC),
        ),
    ]

    async with TestSessionLocal() as session:
        for payment in payments:
            session.add(payment)
        await session.commit()

    return payments
