import json
import os

from aiokafka import AIOKafkaProducer

from notification_app.core.logger import logger

producer: AIOKafkaProducer | None = None


async def startup_kafka():
    global producer
    kafka_url = os.getenv("KAFKA_BROKER", "kafka:9092")
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_url,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")
    )
    try:
        await producer.start()
        logger.info("Kafka producer started.")
    except Exception as e:
        logger.exception("Error initializing Kafka producer")


async def shutdown_kafka():
    global producer
    if producer:
        await producer.stop()
        logger.info("Kafka producer stopped.")


async def send_to_kafka(topic: str, message: dict):
    if not producer:
        raise RuntimeError(
            "Kafka producer is not initialized. Call startup_kafka() first."
        )
    try:
        await producer.send_and_wait(topic, message)
        logger.info(
            f"Message sent to Kafka: topic={topic}, message={message}"
        )
    except Exception as e:
        logger.exception("Error sending message to Kafka")
        raise
