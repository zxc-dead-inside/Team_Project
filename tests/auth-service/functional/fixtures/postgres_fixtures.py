import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from settings import test_settings
from utils.helpers import setup_logger

logger = setup_logger("postgres_fixtures")

Base = declarative_base()

logger.info(f"database_url: {test_settings.database_url}")
async_engine = create_async_engine(test_settings.database_url)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(test_settings.database_url)
    yield engine
    await engine.dispose()


#@pytest.fixture
@pytest.fixture(scope="session")
async def db_session():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.run_sync(Base.metadata.create_all)

        yield session

        await session.rollback()
        await session.run_sync(Base.metadata.drop_all)
