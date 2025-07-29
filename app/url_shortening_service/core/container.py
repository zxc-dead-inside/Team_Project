import redis
from dependency_injector import containers, providers
from services.url_service import URLService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from utils.short_code import ShortCodeGenerator

from core.logging import get_logger
from core.settings import settings


logger = get_logger(__name__)


def create_redis_client():
    """Create Redis client with error handling"""
    try:
        client = redis.from_url(
            settings.redis_url,
            db=settings.redis_db,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        # Test connection
        client.ping()
        logger.info("Redis connection established")
        return client
    except Exception as e:
        logger.warning("Redis connection failed, continuing without caching", error=str(e))
        return None


class Container(containers.DeclarativeContainer):
    """Dependency injection container"""

    # Configuration
    config = providers.Configuration()

    # Database
    db_engine = providers.Singleton(
        create_engine,
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=settings.debug,
        pool_pre_ping=True,
    )

    db_session_factory = providers.Singleton(
        sessionmaker, autocommit=False, autoflush=False, bind=db_engine
    )

    # Redis (with fallback to None if connection fails)
    redis_client = providers.Singleton(create_redis_client)

    # Utils
    short_code_generator = providers.Singleton(
        ShortCodeGenerator, length=settings.short_code_length
    )

    # Services
    url_service = providers.Factory(
        URLService,
        session_factory=db_session_factory,
        redis_client=redis_client,
        short_code_generator=short_code_generator,
    )
