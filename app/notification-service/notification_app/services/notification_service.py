from notification_app.models.models import DeliveryMethod
from notification_app.kafka_producer.producer import send_to_kafka
from notification_app.schemas.event import (
    IncomingEvent,
    FixedEvent,
    BroadcastMessage,
    PersonalizedBatch,
)


class NotificationService:
    @staticmethod
    async def send_message(
        recipient: str, subject: str | None,
        content: str, delivery_method: DeliveryMethod
    ) -> bool:
        message = {
            "user_id": recipient,
            "template_id": None,
            "subject": subject,
            "content": content,
            "delivery_method": delivery_method,
            "source": "admin_event"
        }
        await send_to_kafka("notification.send", message)
        return True

    @staticmethod
    async def handle_custom_event(event: IncomingEvent) -> dict:
        message = {
            "user_id": event.user_id,
            "template_id": event.template_id,
            "data": event.data or {},
            "source": "custom_event"
        }
        await send_to_kafka("notification.send", message)
        return message

    @staticmethod
    async def handle_fixed_event(event: FixedEvent) -> dict:
        message = {
            "event_type": event.type,
            "data": event.data or {},
            "source": "fixed_event"
        }

        await send_to_kafka("notification.send", message)
        return message

    @staticmethod
    async def send_broadcast(msg: BroadcastMessage) -> dict:
        message = {
            "target": "all",
            "template_id": msg.template_id,
            "data": msg.data or {},
            "source": "broadcast"
        }
        await send_to_kafka("notification.send", message)
        return message

    @staticmethod
    async def send_personalized(batch: PersonalizedBatch) -> int:
        for msg in batch.messages:
            message = {
                "user_id": msg.user_id,
                "template_id": msg.template_id,
                "data": msg.data or {},
                "source": "personalized"
            }
            await send_to_kafka("notification.send", message)
        return len(batch.messages)
