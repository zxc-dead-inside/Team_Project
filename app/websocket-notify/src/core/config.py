from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.logger import setup_logging

setup_logging()


class Settings(BaseSettings):
    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug_mode: bool = False
    app_title: str = "WebSocket Notification Worker"
    app_description: str = (
        "Microservice for handling real-time push notifications via WebSocket"
    )
    max_tries: int = 3
    max_seconds: int = 8
        
    # Auth
    auth_service_url: str = "http://auth_service_api:8100"
    validate_token_path: str = "/api/v1/auth/validate-token"
    
    # Kafka
    kafka_bootstrap_servers: str = "kafka-0:9092"
    kafka_group_id: str = "websocket-group"
    kafka_notification_topic: str = "notification.send"
    kafka_dlq_topic: str = "notification.dlq"
    
    # Redis
    redis_url: str = "redis://redis:6379"
    redis_ttl: int = 3600
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        case_sensitive=False
    )

@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()