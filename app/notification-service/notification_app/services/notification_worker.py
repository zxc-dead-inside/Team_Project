import asyncio
import json
import os
from aiokafka import AIOKafkaConsumer
import httpx
from jinja2 import Template
from notification_app.core.logger import logger
from notification_app.models.models import DeliveryMethod

KAFKA_TOPIC = "notification.send"
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BROKER", "kafka:9092")
KAFKA_GROUP_ID = "notification_worker_group"
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service_api:8000")

async def fetch_user(user_id):
    url = f"{AUTH_SERVICE_URL}/api/v1/users/{user_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 200:
            return resp.json()
        logger.error(f"Не удалось получить пользователя {user_id}: {resp.text}")
        return None

async def fetch_template(template_id):
    from notification_app.services.services import MessageTemplateService
    from notification_app.core.database import get_db
    async for db in get_db():
        template = await MessageTemplateService.get_template(db, template_id)
        if template:
            return template.content
        return None

async def send_email(message: dict):
    logger.info(f"[EMAIL] Отправка email: {message}")
    await asyncio.sleep(0.1)

async def send_sms(message: dict):
    logger.info(f"[SMS] Отправка sms: {message}")
    await asyncio.sleep(0.1)

async def send_push(message: dict):
    logger.info(f"[PUSH] Отправка push: {message}")
    await asyncio.sleep(0.1)

def safe_deserializer(v):
    if v is None or v == b'':
        return None
    try:
        return json.loads(v.decode('utf-8'))
    except Exception as e:
        logger.error(f"Ошибка десериализации: {e}")
        return None

async def worker():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        value_deserializer=safe_deserializer,
        enable_auto_commit=False
    )
    
    max_retries = 30
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            await consumer.start()
            logger.info(f"Kafka consumer запущен для топика: {KAFKA_TOPIC}")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Попытка подключения к Kafka {attempt + 1}/{max_retries} не удалась: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Не удалось подключиться к Kafka после {max_retries} попыток")
                return
    
    try:
        async for msg in consumer:
            message = msg.value
            if not message:
                logger.warning(f"Пустое/невалидное сообщение на offset {msg.offset}. Пропускаю.")
                await consumer.commit()
                continue
            user_id = message.get("user_id")
            template_id = message.get("template_id")
            delivery_method = message.get("delivery_method")
            if not user_id or not template_id or not delivery_method:
                logger.warning(f"Нет user_id/template_id/delivery_method в сообщении: {message}")
                await consumer.commit()
                continue
            user = await fetch_user(user_id)
            if not user:
                await consumer.commit()
                continue
            template_content = await fetch_template(template_id)
            if not template_content:
                logger.warning(f"Шаблон {template_id} не найден")
                await consumer.commit()
                continue
            rendered = Template(template_content).render(**user)
            message["content"] = rendered
            if delivery_method == DeliveryMethod.EMAIL:
                await send_email(message)
            elif delivery_method == DeliveryMethod.SMS:
                await send_sms(message)
            elif delivery_method == DeliveryMethod.PUSH:
                await send_push(message)
            else:
                logger.warning(f"Неизвестный способ доставки: {delivery_method}")
            await consumer.commit()
    except Exception as e:
        logger.error(f"Ошибка воркера: {e}", exc_info=True)
    finally:
        await consumer.stop()
        logger.info("Kafka consumer остановлен")

if __name__ == "__main__":
    asyncio.run(worker()) 