"""
Database Connection and Session Management

This module sets up the async SQLAlchemy engine and session factory for PostgreSQL.
It uses the asyncpg driver for high-performance async database operations.

Architecture:
- AsyncEngine: Manages connection pool to PostgreSQL
- async_sessionmaker: Factory for creating database sessions
- get_db: Dependency injection function for FastAPI routes

Connection pooling is configured for handling concurrent requests efficiently.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import get_settings

settings = get_settings()

# Create async engine with connection pool settings optimized for concurrent requests
# - pool_size: Number of connections to maintain in the pool
# - max_overflow: Additional connections allowed beyond pool_size
# - pool_pre_ping: Verify connections are alive before using them
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=10,  # Base number of connections
    max_overflow=20,  # Allow up to 30 total connections under load
    pool_pre_ping=True,  # Health check connections before use
)

# Session factory for creating database sessions
# - expire_on_commit=False: Keep objects accessible after commit
# - class_=AsyncSession: Use async session class
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function to provide database sessions.

    This is used as a FastAPI dependency to inject database sessions into
    route handlers and GraphQL resolvers. The session is automatically
    closed when the request completes.

    Yields:
        AsyncSession: Database session for the current request

    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined by models that inherit from Base.
    This should be called once at application startup.

    Note: In production, use Alembic migrations instead of create_all().
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.

    Disposes of the connection pool. Should be called at application shutdown.
    """
    await engine.dispose()
