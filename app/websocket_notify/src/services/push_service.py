import json
import logging

import backoff
from aiokafka import AIOKafkaProducer

from src.core.config import get_settings
from src.core.exceptions import PushDeliveryException
from src.core.logger import setup_logging
from src.services.connection_manager import ConnectionManager
from src.services.redis import RedisService

setup_logging()
settings = get_settings()

def on_backoff(details):
    """Callback при срабатывании backoff"""

    message_id = details['args'][0]
    attempt = details['tries']
    delay = details['wait']
    logging.warning(
        f"Retrying message {message_id}, "
        f"attempt {attempt}, delay {delay:.2f}s"
    )

def on_giveup(details):
    """Callback при достижении максимального числа попыток"""

    message_id = details['args'][0]
    logging.error(
        f"Giving up on message {message_id} after {details['tries']} attempts"
    )
    raise PushDeliveryException()

class PushService:
    def __init__(
        self,
        connection_manager: ConnectionManager,
        kafka_producer: AIOKafkaProducer,
        redis_service: RedisService,
        dlq_topic: str
    ):
        self.manager = connection_manager
        self.kafka_producer = kafka_producer
        self.dlq_topic = dlq_topic
        self.redis_service = redis_service

    async def process_message(self, message: dict):
        try:
            await self._send_with_backoff(
                message["message_id"],
                message["user_id"],
                {"title": message["subject"],
                "body": message["content"]},
            )
            await self.reset_retry_count(message["message_id"])
        except PushDeliveryException:
            await self.send_to_dlq(message)

    @backoff.on_exception(
        backoff.expo, 
        Exception, 
        max_tries=settings.max_tries,
        max_value=settings.max_seconds,
        jitter=backoff.full_jitter,
        on_backoff=on_backoff,
        on_giveup=on_giveup
    )
    async def _send_with_backoff(
        self, 
        message_id: str,
        user_id: str, 
        payload: str
        ):
        """Пытаемся отправить сообщение с экспоненциальной задержкой"""

        logging.info(f"Message id: {message_id}")
        logging.info(f"User id: {user_id}")
        logging.info(f"Payload: {payload}")

        retry_count = await self.increment_retry_count(message_id)
        
        if retry_count > 3:
            raise PushDeliveryException("Max retries exceeded")
        
        try:
            await self.manager.send_personal_message(user_id, payload)
            logging.info(f"Message delivered to user {user_id}")
        except Exception as e:
            logging.warning(f"Failed to send message to {user_id}: {str(e)}")
            raise

    async def increment_retry_count(self, message_id: str) -> int:
        """Увеличивает счетчик попыток обработки сообщения"""

        key = f"retry:{message_id}"
        return await self.redis_service.incr(key)

    async def get_retry_count(self, message_id: str) -> int:
        """Возвращает текущее количество попыток"""

        key = f"retry:{message_id}"
        count = await self.redis_service.get(key)
        return int(count) if count else 0

    async def reset_retry_count(self, message_id: str):
        """Сбрасывает счетчик попыток"""

        key = f"retry:{message_id}"
        await self.redis_service.delete(key)

    async def send_to_dlq(self, message: dict):
        """Отправка сообщения в Dead Letter Queue в Kafka"""

        try:
            await self.kafka_producer.send(
                self.dlq_topic,
                value=json.dumps(message).encode("utf-8")
            )
            logging.info(f"Message {message['message_id']} sent to DLQ")
        except Exception as e:
            logging.error(f"Failed to send message to DLQ: {str(e)}")