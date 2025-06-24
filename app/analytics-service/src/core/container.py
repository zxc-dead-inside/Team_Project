"""Dependency injection container for the application."""

from dependency_injector import containers, providers
from src.core.config import Settings
from src.services.kafka import KafkaProducer
from src.services.kafka.producer import KafkaEventSender


class Container(containers.DeclarativeContainer):
    """Application container for dependency injection."""

    config = providers.Configuration()

    @classmethod
    def init_config_from_settings(cls, container, settings: Settings):
        """Initialize configuration from settings."""
        container.config.set("environment", settings.environment)
        container.config.set("log_level", settings.log_level)

        container.config.set(
            "kafka_bootstrap_servers", settings.kafka_bootstrap_servers
        )
        container.config.set("kafka_topic", settings.kafka_topic)
        container.config.set("kafka_username", settings.kafka_username)
        container.config.set("kafka_password", settings.kafka_password)
        container.config.set("retry_max_attempts", settings.retry_max_attempts)
        container.config.set("retry_base_delay", settings.retry_base_delay)

    # Kafka producer
    kafka_producer = providers.Singleton(
        KafkaProducer, bootstrap_servers=config.kafka_bootstrap_servers
    )

    event_sender = providers.Factory(
        KafkaEventSender,
        producer=kafka_producer,
        topic=config.kafka_topic,
        retry_max_attempts=config.retry_max_attempts,
        retry_base_delay=config.retry_base_delay,
    )
