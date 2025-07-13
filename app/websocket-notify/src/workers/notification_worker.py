import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from src.core.logger import setup_logging
from src.services.push_service import PushService

setup_logging()


class KafkaWorker:
    def __init__(
        self,
        push_service: PushService,
        kafka_producer: AIOKafkaProducer,
        kafka_notification_topic: str,
        kafka_bootstrap_servers: str,
        kafka_group_id: str,
    ):
        self.push_service = push_service
        self.kafka_producer = kafka_producer
        self.kafka_notification_topic = kafka_notification_topic
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.kafka_group_id = kafka_group_id

    async def start(self):
        """Запускает Kafka Consumer."""

        def safe_deserializer(v):
            """Проверят чтобы сообщение в кафка было не пустым"""

            if v is None or v == b'':
                return None
            try:
                return json.loads(v.decode('utf-8'))
            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                logging.error(f"Deserialization error: {str(e)}")
                return None

        consumer = AIOKafkaConsumer(
            self.kafka_notification_topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id=self.kafka_group_id,
            value_deserializer=safe_deserializer,
            enable_auto_commit=False
        )
    
        try:
            await consumer.start()
            logging.info(
                "Kafka consumer started for topic: "
                f"{self.kafka_notification_topic}"
            )
            
            async for msg in consumer:
                try:
                    message = msg.value
                    if not message:
                        logging.warning(
                            "Empty/invalid message at offset "
                            f"{msg.offset}. Skipping"
                        )
                        await consumer.commit()
                        continue

                    if message.get("delivery_method") == "push":
                        logging.debug(
                            f"Processing push notification: {message}"
                        )
                        asyncio.create_task(
                            self.push_service.process_message(message)
                        )
                    
                    await consumer.commit()
                except Exception as e:
                    logging.error(
                        f"Error processing message: {str(e)}", exc_info=True
                    )
                    await asyncio.sleep(1)

        except Exception as e:
            logging.exception("Kafka worker fatal error")
        finally:
            await consumer.stop()
            logging.info("Kafka consumer stopped")
