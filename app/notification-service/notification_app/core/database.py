import os

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from notification_app.models.models import Base

database_url = os.getenv(
    "DATABASE_URL",
    "postgresql://notification_user:notification_pass@localhost:5432/notification_db",
)

if not database_url.startswith("postgresql+asyncpg"):
    # Automatically convert sync psycopg url to asyncpg url if needed
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine and session factory
engine = create_async_engine(database_url, future=True, echo=False)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
)


async def get_db():
    """FastAPI dependency that yields an ``AsyncSession`` instance."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_models() -> None:
    """Create database tables asynchronously."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
