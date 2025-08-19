"""Dependency injection container for the application."""

from dependency_injector import containers, providers
from src.core.config import Settings
from src.db.database import Database
from src.db.repositories.audit_log_repository import AuditLogRepository
from src.db.repositories.login_history_repository import LoginHistoryRepository
from src.db.repositories.role_repository import RoleRepository
from src.db.repositories.transaction_repository import (
    SubscriptionRepository,
    TransactionRepository,
)
from src.db.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.billing_service import BillingService
from src.services.email_verification_service import EmailService
from src.services.oauth.oauth_service import OAuthService
from src.services.oauth.providers import VKOAuthProvider, YandexOAuthProvider
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

        # OAuth providers
        container.config.set("yandex_client_id", str(settings.yandex_client_id))
        container.config.set("yandex_client_secret", str(settings.yandex_client_secret))
        container.config.set("yandex_redirect_uri", str(settings.yandex_redirect_uri))
        container.config.set("yandex_oauth_url", str(settings.yandex_oauth_url))
        container.config.set("yandex_token_url", str(settings.yandex_token_url))
        container.config.set("yandex_user_info_url", str(settings.yandex_user_info_url))

        container.config.set("vk_client_id", str(settings.vk_client_id))
        container.config.set("vk_client_secret", str(settings.vk_client_secret))
        container.config.set("vk_redirect_uri", str(settings.vk_redirect_uri))
        container.config.set("vk_oauth_url", str(settings.vk_oauth_url))
        container.config.set("vk_token_url", str(settings.vk_token_url))
        container.config.set("vk_user_info_url", str(settings.vk_user_info_url))

        container.config.set("oauth_state_ttl", str(settings.oauth_state_ttl))
        
        # Billing settings
        container.config.set("payment_service_url", settings.payment_service_url)
        container.config.set("http_client_timeout", settings.http_client_timeout)

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

    transaction_repository = providers.Factory(
        TransactionRepository,
        session_factory=db.provided.session,
    )

    subscription_repository = providers.Factory(
        SubscriptionRepository,
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
        cache_service=redis_service,
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

    yandex_config = providers.Dict(
        {
            "client_id": config.yandex_client_id,
            "client_secret": config.yandex_client_secret,
            "redirect_uri": config.yandex_redirect_uri,
            "auth_url": config.yandex_oauth_url,
            "token_url": config.yandex_token_url,
            "user_info_url": config.yandex_user_info_url,
        }
    )

    vk_config = providers.Dict(
        {
            "client_id": config.vk_client_id,
            "client_secret": config.vk_client_secret,
            "redirect_uri": config.vk_redirect_uri,
            "auth_url": config.vk_oauth_url,
            "token_url": config.vk_token_url,
            "user_info_url": config.vk_user_info_url,
        }
    )

    yandex_provider = providers.Factory(YandexOAuthProvider, config=yandex_config)

    vk_provider = providers.Factory(VKOAuthProvider, config=vk_config)

    provider_factory = providers.Dict({"yandex": yandex_provider, "vk": vk_provider})

    oauth_service = providers.Factory(
        OAuthService,
        provider_factory=provider_factory,
        redis_service=redis_service,
        user_repository=user_repository,
        state_ttl=config.oauth_state_ttl,
    )

    user_service = providers.Factory(
        UserService,
        user_repository=user_repository,
        login_history_repository=login_history_repository,
        role_repository=role_repository,
        auth_service=auth_service,
        redis_service=redis_service,
        oauth_service=oauth_service,
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

    # Create a settings provider for billing service
    settings_provider = providers.Singleton(Settings)

    billing_service = providers.Factory(
        BillingService,
        settings=settings_provider,
        transaction_repo=transaction_repository,
        subscription_repo=subscription_repository,
    )
