"""Dependency injection container for the application."""

from dependency_injector import containers, providers
from src.core.config import Settings
from src.services.kafka import KafkaProducer


class Container(containers.DeclarativeContainer):
    """Application container for dependency injection."""

    config = providers.Configuration()
    
    @classmethod
    def init_config_from_settings(cls, container, settings: Settings):
        """Initialize configuration from settings."""
        container.config.set("environment", settings.environment)
        container.config.set("log_level", settings.log_level)

        container.config.set(
            "kafka_boostrap_servers", settings.kafka_boostrap_servers)
        container.config.set("kafka_topic", settings.kafka_topic)
        container.config.set("kafka_username", settings.kafka_username)
        container.config.set("kafka_password", settings.kafka_password)


    # Kafka producer
    kafka_producer = providers.Singleton(
        KafkaProducer,
        bootstrap_servers=config.kafka_boostrap_servers
    )
