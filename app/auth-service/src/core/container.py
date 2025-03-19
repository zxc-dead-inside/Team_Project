"""Dependency injection container for the application."""

from dependency_injector import containers, providers
from src.core.config import Settings
from src.db.database import Database
from src.db.repositories.audit_log_repository import AuditLogRepository
from src.db.repositories.login_history_repository import LoginHistoryRepository
from src.db.repositories.role_repository import RoleRepository
from src.db.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.email_verification_service import EmailService
from src.services.redis_service import RedisService
from src.services.reset_password_service import ResetPasswordService
from src.services.role_service import RoleService
from src.services.superuser_service import SuperuserService
from src.services.user_service import UserService


class Container(containers.DeclarativeContainer):
    """Application container for dependency injection."""

    config = providers.Configuration()
    
    @classmethod
    def init_config_from_settings(cls, container, settings: Settings):
        """Initialize configuration from settings."""
        container.config.set("environment", settings.environment)
        container.config.set("log_level", settings.log_level)
        container.config.set("public_key", settings.public_key)
        container.config.set("private_key", settings.private_key)
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
        container.config.set("max_requests_per_ttl", int(settings.max_requests_per_ttl))
        container.config.set("reset_token_ttl", int(settings.reset_token_ttl))
        container.config.set("redis_url", str(settings.redis_url))
        container.config.set("cache_ttl", 3600)  # 1 hour default for cache TTL

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

    login_history_repository = providers.Factory(
        LoginHistoryRepository,
        session_factory=db.provided.session,
    )

    role_repository = providers.Factory(
        RoleRepository,
        session_factory=db.provided.session,
    )

    audit_log_repository = providers.Factory(
        AuditLogRepository,
        session_factory=db.provided.session,
    )

    # Services
    redis_service = providers.Singleton(
        RedisService,
        redis_url=config.redis_url,
        default_ttl=config.cache_ttl,
    )

    email_service = providers.Factory(
        EmailService,
        public_key=config.public_key,
        private_key=config.private_key,
        email_token_ttl_seconds=config.email_token_ttl_seconds,
    )

    reset_password_service = providers.Factory(
        ResetPasswordService,
        user_repository=user_repository,
        public_key=config.public_key,
        private_key=config.private_key,
        reset_token_ttl=config.reset_token_ttl,
        max_requests_per_ttl=config.max_requests_per_ttl,
        cache_service=redis_service
    )

    auth_service = providers.Factory(
        AuthService,
        user_repository=user_repository,
        public_key=config.public_key,
        private_key=config.private_key,
        access_token_expire_minutes=config.access_token_expire_minutes,
        refresh_token_expire_days=config.refresh_token_expire_days,
        email_service=email_service,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        login_history_repository=login_history_repository,
        role_repository=role_repository,
        auth_service=auth_service,
        redis_service=redis_service,
    )

    role_service = providers.Factory(
        RoleService,
        role_repository=role_repository,
        redis_service=redis_service,
    )

    superuser_service = providers.Factory(
        SuperuserService,
        user_repository=user_repository,
        audit_log_repository=audit_log_repository,
    )
