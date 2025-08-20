from dependency_injector import containers, providers
from services.url_service import URLService
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from utils.short_code import ShortCodeGenerator

from core.logging import get_logger
from core.settings import settings


logger = get_logger(__name__)


class Container(containers.DeclarativeContainer):
    """Dependency injection container"""

    # Configuration
    config = providers.Configuration()

    # Async Database
    async_db_engine = providers.Singleton(
        create_async_engine,
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.debug,
        pool_pre_ping=True,
    )

    async_db_session_factory = providers.Singleton(
        async_sessionmaker,
        bind=async_db_engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    # Utils
    short_code_generator = providers.Singleton(
        ShortCodeGenerator, length=settings.short_code_length
    )

    # Services
    url_service = providers.Factory(
        URLService,
        session_factory=async_db_session_factory,
        short_code_generator=short_code_generator,
    )
