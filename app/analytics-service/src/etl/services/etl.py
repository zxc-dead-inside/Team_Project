import asyncio
import logging
from typing import Any

from src.etl.services.consumer import KafkaConsumer
from src.etl.services.clickhouse import ClickHouseClient
from src.core.logger import setup_logging

setup_logging()


class AnalyticsETLService:
    """ETL service for analytics data pipeline."""
    
    def __init__(
        self,
        kafka_consumer: KafkaConsumer,
        clickhouse_client: ClickHouseClient,
    ):
        """Initialize ETL service.
        
        Args:
            kafka_consumer: Configured Kafka consumer
            clickhouse_client: Configured ClickHouse client
        """
        self.kafka_consumer = kafka_consumer
        self.clickhouse_client = clickhouse_client
        self.running = False
        
        logging.info("Initialized Analytics ETL service")
    
    async def start(self) -> None:
        """Start the ETL service."""
        if self.running:
            return
            
        self.running = True
        
        # Initialize ClickHouse tables
        self.clickhouse_client.create_tables()
        
        # Start Kafka consumer
        await self.kafka_consumer.start()
        
        # Start consumption
        asyncio.create_task(self._consume_forever())
        
        logging.info("Started Analytics ETL service")
    
    async def stop(self) -> None:
        """Stop the ETL service."""
        if not self.running:
            return
            
        self.running = False
        await self.kafka_consumer.stop()
        
        logging.info("Stopped Analytics ETL service")
    
    async def healthcheck(self) -> dict[str, Any]:
        """Check if ETL service is healthy.
        
        Returns:
            Dict with status and details
        """
        if not self.running:
            return {"status": False, "detail": "ETL service is not running"}
            
        # Check Kafka consumer
        kafka_status = await self.kafka_consumer.healthcheck()
        if not kafka_status["status"]:
            return {"status": False,
                    "detail": f"Kafka consumer: {kafka_status['detail']}"}
            
        # Check ClickHouse
        clickhouse_status = await self.clickhouse_client.healthcheck()
        if not clickhouse_status["status"]:
            return {"status": False,
                    "detail": f"ClickHouse: {clickhouse_status['detail']}"}
            
        return {"status": True, "detail": ""}
    
    def _process_batch(self, messages: list[dict[str, Any]]) -> int | None:
        """Process a batch of messages from Kafka.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Number of messages processed
        """
        try:
            inserted = self.clickhouse_client.insert_user_actions(messages)
            return inserted
        except Exception as e:
            logging.error(f"Error processing batch: {e}")
            return None
    
    async def _consume_forever(self) -> None:
        """Continuously consume and process messages."""
        await self.kafka_consumer.consume_forever(self._process_batch)
