import json
import logging

import backoff
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
from src.core.logger import setup_logging


setup_logging()


class KafkaProducer(AIOKafkaProducer):
    """Wraper for AIOKafkaProducer"""

    def __init__(self, bootstrap_servers):
        super().__init__(bootstrap_servers=bootstrap_servers)

    async def healthcheck(self):
        if not self.client or not self.client._conns:
            return {"status": False, "detail": "Kafka producer is not ready"}
        if not self.client.cluster.brokers():
            return {"status": False, "detail": "No brokers available"}
        return {"status": True, "detail": ""}


class KafkaEventSender:
    """Class for sending data to kafka"""

    def __init__(self, producer, topic, retry_max_attempts, retry_base_delay):
        self.producer = producer
        self.topic = topic
        self.retry_max_attempts = retry_max_attempts
        self.retry_base_delay = retry_base_delay

    @backoff.on_exception(
        backoff.expo,
        KafkaError,
        max_tries=10,
        base=0.1,
        logger=logging.getLogger(__name__),
    )
    async def send_event(self, message: dict):
        """
        Send an event to Kafka with retry logic.

        Args:
            producer: AIOKafkaProducer instance
            event: User action event to send
            topic: Kafka topic name

        Raises:
            Exception: If message fails to send after retries
        """
        try:
            await self.producer.send(
                self.topic, value=json.dumps(message).encode("utf-8")
            )
        except KafkaError as err:
            logging.error(f"Failed to send message: {err}")
            raise
