import json

from aiokafka import AIOKafkaConsumer

from template_worker.core.database import get_database
from template_worker.core.logger import logger
from template_worker.core.settings import get_settings
from template_worker.db.repositories.template_repository import \
    MessageTemplateRepository
from template_worker.kafka_service.producer import send_to_kafka
from template_worker.service.grpc_service import get_user_info_rpc
from template_worker.service.template_service import TemplateService


async def listen_to_kafka(consumer: AIOKafkaConsumer, template_service: TemplateService):
    async for msg in consumer:
        try:
            message = json.loads(msg.value)
            user_id = message.get("user_id")
            user_info = await get_user_info_rpc(user_id)
            template_id = message.get("template_id")
            data = message.get("data", {})
            data.update(user_info)
            content = await template_service.apply_template(template_id, data)
            message['content'] = content
            message['user'] = user_info

            await send_to_kafka("processed_notifications", message)

        except Exception as e:
            logger.error(f"error creating msg: {e}")


async def start_kafka_consumer():
    settings = get_settings()
    db = get_database(settings.database_url)
    template_repo = MessageTemplateRepository(db.session_factory)
    template_service = TemplateService(template_repo)

    consumer = AIOKafkaConsumer(
        "notification.send",
        bootstrap_servers="localhost:9092",
        group_id="notification_worker_group",
    )

    await consumer.start()
    try:
        await listen_to_kafka(consumer, template_service)
    except Exception as e:
        logger.error(f"Error with Kafka consumer: {str(e)}")
    finally:
        await consumer.stop()
