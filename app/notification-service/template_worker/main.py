import asyncio

from template_worker.core.database import get_database
from template_worker.core.settings import get_settings
from template_worker.db.repositories.template_repository import \
    MessageTemplateRepository
from template_worker.service.template_service import TemplateService


async def main():
    settings = get_settings()
    db = get_database(settings.database_url)
    template_repo = MessageTemplateRepository(db.session_factory)
    template_service = TemplateService(template_repo)

    event = IncomingEvent(user_id="123", template_id=1, data={"key": "value"})
    result = await notification_service.handle_custom_event(event, template_service)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_kafka_consumer())
