from aiokafka import AIOKafkaProducer
from dependency_injector import containers, providers

from src.core.config import Settings
from src.services.connection_manager import ConnectionManager
from src.services.push_service import PushService
from src.services.redis import RedisService
from src.workers.notification_worker import KafkaWorker


class Container(containers.DeclarativeContainer):
    
    config = providers.Configuration()
    
    @classmethod
    def init_config_from_settings(cls, container, settings: Settings):
        container.config.set(
            "bootstrap_servers", settings.kafka_bootstrap_servers
        )
        container.config.set("dlq_toic", settings.kafka_dlq_topic)
        container.config.set("redis_url", settings.redis_url)
        container.config.set("redis_ttl", settings.redis_ttl)
        container.config.set(
            "kafka_notification_topic", settings.kafka_notification_topic
        )
        container.config.set("kafka_group_id", settings.kafka_group_id)


    redis_service = providers.Singleton(
        RedisService,
        redis_url=config.redis_url,
        default_ttl=config.redis_ttl,
    )

    connection_manager = providers.Singleton(
        ConnectionManager,
        redis_service=redis_service,
    )

    kafka_producer = providers.Singleton(
        AIOKafkaProducer,
        bootstrap_servers=config.bootstrap_servers
    )
    
    push_service = providers.Factory(
        PushService,
        connection_manager=connection_manager,
        kafka_producer=kafka_producer,
        redis_service=redis_service,
        dlq_topic=config.dlq_topic,
    )
    
    kafka_worker = providers.Singleton(
        KafkaWorker,
        push_service=push_service,
        kafka_producer=kafka_producer,
        kafka_notification_topic=config.kafka_notification_topic,
        kafka_bootstrap_servers=config.bootstrap_servers,
        kafka_group_id=config.kafka_group_id,
    )
    
