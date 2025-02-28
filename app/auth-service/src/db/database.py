"""Database configuration and session management."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool
from src.db.base_models import Base


class Database:
    """Database session manager."""

    def __init__(
        self,
        db_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 1800,
    ):
        """Initialize the database with the given URL and pool settings."""

        db_url = self._ensure_async_driver(db_url)
        self._engine = create_async_engine(
            db_url,
            echo=echo,
            future=True,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )
        self._session_factory = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self._engine,
            expire_on_commit=False,
        )

    def _ensure_async_driver(self, db_url: str) -> str:
        """Ensure the database URL uses the async driver."""

        if "+asyncpg" in db_url:
            return db_url

        if db_url.startswith("postgresql://"):
            return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        return db_url

    async def create_database(self) -> None:
        """Create all tables defined in the models."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Create a new database session.

        Yields:
            AsyncSession: Database session
        """
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def check_connection(self) -> bool:
        """
        Check if the database connection is healthy.

        Returns:
            bool: True if the connection is healthy, False otherwise
        """
        try:
            async with self._engine.connect() as conn:
                result = await conn.execute(sa.text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            import logging

            logging.error(f"Database connection error: {e}")
            return False

    @property
    def session_factory(self) -> Callable[[], AsyncSession]:
        """Return the session factory."""
        return self._session_factory

    @property
    def engine(self) -> AsyncEngine:
        """Return the engine."""
        return self._engine

    async def dispose(self) -> None:
        """Dispose of the engine."""
        await self._engine.dispose()


# Singleton pattern (optional)
_db_instance: Database | None = None


def get_database(db_url: str) -> Database:
    """
    Get or create a database instance.

    Args:
        db_url: Database URL to connect to

    Returns:
        Database: Database instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_url)
    return _db_instance


@asynccontextmanager
async def get_db_session(db: Database) -> AsyncGenerator[AsyncSession, None]:
    """
    Get a database session from the provided Database instance.

    Args:
        db: Database instance

    Yields:
        AsyncSession: Database session
    """
    async with db.session() as session:
        yield session
