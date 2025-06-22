import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

import backoff
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from src.core.logger import setup_logging


setup_logging()


class KafkaConsumer:
    """Kafka consumer for analytics data."""

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        batch_size: int = 100,
        batch_timeout: float = 5.0,
    ):
        """Initialize Kafka consumer.

        Args:
            bootstrap_servers: Comma-separated list of Kafka broker addresses
            topic: Kafka topic to consume from
            group_id: Consumer group ID
            batch_size: Maximum number of messages to process in a batch
            batch_timeout: Maximum time to wait for a batch to fill (seconds)
        """
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.consumer = None
        self.running = False

        logging.info(
            f"Initialized Kafka consumer for topic {topic} with group {group_id}"
        )

    async def start(self) -> None:
        """Start the Kafka consumer."""
        if self.consumer is not None:
            return

        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )

        await self.consumer.start()
        self.running = True
        logging.info(f"Started Kafka consumer for topic {self.topic}")

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self.consumer is None:
            return

        self.running = False
        await self.consumer.stop()
        self.consumer = None
        logging.info(f"Stopped Kafka consumer for topic {self.topic}")

    async def healthcheck(self) -> dict[str, Any]:
        """Check if Kafka consumer is healthy.

        Returns:
            Dict with status and details
        """
        if not self.consumer or not self.running:
            return {"status": False, "detail": "Kafka consumer is not running"}

        try:
            # Check if we can get the topic partitions
            partitions = await self.consumer.partitions_for_topic(self.topic)
            if partitions is None:
                return {"status": False, "detail": f"Topic {self.topic} does not exist"}
            return {"status": True, "detail": ""}
        except Exception as e:
            return {"status": False, "detail": str(e)}

    @backoff.on_exception(
        backoff.expo,
        KafkaError,
        max_tries=5,
        base=1,
        logger=logging.getLogger(__name__),
    )
    async def consume_batch(
        self, processor: Callable[[list[dict[str, Any]]], int | None]
    ) -> int:
        """Consume a batch of messages and process them.

        Args:
            processor: Function to process the batch of messages

        Returns:
            Number of messages processed

        Raises:
            KafkaError: If there's an error consuming from Kafka
        """
        if not self.consumer or not self.running:
            logging.error("Cannot consume: consumer is not running")
            return 0

        batch = []
        total_processed = 0

        try:
            start_time = asyncio.get_event_loop().time()

            async for message in self.consumer:
                batch.append(message.value)

                # Process batch if reached batch size or timeout
                current_time = asyncio.get_event_loop().time()
                if (
                    len(batch) >= self.batch_size
                    or current_time - start_time >= self.batch_timeout
                ):
                    processed = processor(batch)
                    if processed:
                        total_processed += processed

                    await self.consumer.commit()

                    batch = []
                    start_time = current_time

                # Check if we should continue running
                if not self.running:
                    break

            # Process any remaining messages in the batch
            if batch:
                processed = processor(batch)
                if processed:
                    total_processed += processed
                await self.consumer.commit()

            return total_processed

        except KafkaError as e:
            logging.error(f"Error consuming from Kafka: {e}")
            raise

    async def consume_forever(
        self, processor: Callable[[list[dict[str, Any]]], int | None]
    ) -> None:
        """Continuously consume messages and process them.

        Args:
            processor: Function to process the batch of messages
        """
        self.running = True

        while self.running:
            try:
                await self.consume_batch(processor)
            except Exception as e:
                logging.error(f"Error in consume_forever: {e}")
                await asyncio.sleep(1)

        logging.info("Stopped continuous consumption")
