"""Dependency injection container for the application."""

from dependency_injector import containers, providers
from src.core.config import Settings
from src.db.database import Database
from src.db.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.redis_service import RedisService


class Container(containers.DeclarativeContainer):
    """Application container for dependency injection."""

    config = providers.Configuration()

    @classmethod
    def init_config_from_settings(cls, container, settings: Settings):
        """Initialize configuration from settings."""
        container.config.set("environment", settings.environment)
        container.config.set("log_level", settings.log_level)
        container.config.set("secret_key", settings.secret_key)
        container.config.set(
            "access_token_expire_minutes", settings.access_token_expire_minutes
        )
        container.config.set(
            "refresh_token_expire_days", settings.refresh_token_expire_days
        )
        container.config.set(
            "email_token_ttl_seconds", settings.email_token_ttl_seconds
        )
        container.config.set("database_url", str(settings.database_url))
        container.config.set("redis_url", str(settings.redis_url))

    # Database
    db = providers.Singleton(
        Database,
        db_url=config.database_url,
    )

    # Repositories
    user_repository = providers.Factory(
        UserRepository,
        session_factory=db.provided.session,
    )

    # Services
    email_service = providers.Factory(
        EmailService,
        secret_key=config.secret_key,
        email_token_ttl_seconds=config.email_token_ttl_seconds,
    )

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        secret_key=config.secret_key,
        access_token_expire_minutes=config.access_token_expire_minutes,
        refresh_token_expire_days=config.refresh_token_expire_days,
        email_service=email_service,
    )

    cache_service = providers.Singleton(
        RedisService,
        redis_url=config.redis_url
    )
