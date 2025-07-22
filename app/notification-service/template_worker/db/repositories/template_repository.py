from sqlalchemy import select

from notification_app.models.models import MessageTemplate


class MessageTemplateRepository:
    def __init__(self, session_factory):
        self._session_factory = session_factory

    # Метод для получения шаблона по ID
    async def get_template_by_id(self, template_id: int) -> MessageTemplate | None:
        async with self._session_factory() as session:
            result = await session.execute(
                select(MessageTemplate).filter(MessageTemplate.id == template_id)
            )
            template = result.scalars().first()
            return template
