from dependency_injector import containers, providers
from src.core.config import Settings
from src.etl.services.clickhouse import ClickHouseClient
from src.etl.services.consumer import KafkaConsumer
from src.etl.services.etl import AnalyticsETLService


class ETLContainer(containers.DeclarativeContainer):
    """Container for ETL service dependencies."""
    
    config = providers.Configuration()

    kafka_consumer = providers.Singleton(
        KafkaConsumer,
        bootstrap_servers=config.kafka_bootstrap_servers,
        topic=config.kafka_topic,
        group_id=config.kafka_group_id,
        batch_size=config.batch_size,
        batch_timeout=config.batch_timeout
    )
    
    clickhouse_client = providers.Singleton(
        ClickHouseClient,
        host=config.clickhouse_host,
        port=config.clickhouse_port,
        user=config.clickhouse_user,
        password=config.clickhouse_password,
        database=config.clickhouse_database
    )
    
    etl_service = providers.Singleton(
        AnalyticsETLService,
        kafka_consumer=kafka_consumer,
        clickhouse_client=clickhouse_client
    )
    
    @classmethod
    def init_config_from_settings(cls, container, settings: Settings):
        """Initialize container configuration from settings.
        
        Args:
            container: Container instance
            settings: Application settings
        """
        container.config.from_dict({
            'kafka_bootstrap_servers': settings.kafka_bootstrap_servers,
            'kafka_topic': settings.kafka_topic,
            'kafka_group_id': settings.kafka_group_id,
            'batch_size': settings.etl_batch_size,
            'batch_timeout': settings.etl_batch_timeout,
            'clickhouse_host': settings.clickhouse_host,
            'clickhouse_port': settings.clickhouse_port,
            'clickhouse_user': settings.clickhouse_user,
            'clickhouse_password': settings.clickhouse_password,
            'clickhouse_database': settings.clickhouse_database
        })
