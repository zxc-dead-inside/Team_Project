import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from notification_app.models.models import (Message, MessageStatus,
                                            MessageTemplate, ScheduledTask)
from notification_app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class MessageTemplateService:
    @staticmethod
    async def create_template(db: AsyncSession, template_data) -> MessageTemplate:
        template = MessageTemplate(**template_data.model_dump())
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def get_templates(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[MessageTemplate]:
        result = await db.execute(select(MessageTemplate).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_template(db: AsyncSession, template_id: int) -> MessageTemplate | None:
        return await db.get(MessageTemplate, template_id)

    @staticmethod
    async def update_template(db: AsyncSession, template_id: int, template_data) -> MessageTemplate | None:
        template = await db.get(MessageTemplate, template_id)
        if template:
            for field, value in template_data.model_dump(exclude_unset=True).items():
                setattr(template, field, value)
            await db.commit()
            await db.refresh(template)
        return template

    @staticmethod
    async def delete_template(db: AsyncSession, template_id: int) -> bool:
        template = await db.get(MessageTemplate, template_id)
        if template:
            db.delete(template)
            await db.commit()
            return True
        return False


class MessageService:
    @staticmethod
    async def create_message(db: AsyncSession, message_data) -> Message:
        message = Message(**message_data.model_dump())
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def send_message_immediately(db: AsyncSession, message: Message) -> bool:
        success = await NotificationService.send_message(
            message.recipient, message.subject, message.content, message.delivery_method
        )
        if success:
            message.status = MessageStatus.SENT
            message.sent_at = datetime.utcnow()
        else:
            message.status = MessageStatus.FAILED
        await db.commit()
        return success  # type: ignore

    @staticmethod
    async def get_messages(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Message]:
        result = await db.execute(select(Message).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_message(db: AsyncSession, message_id: int) -> Message | None:
        return await db.get(Message, message_id)


class ScheduledTaskService:
    @staticmethod
    async def create_scheduled_task(db: AsyncSession, task_data) -> ScheduledTask:
        task = ScheduledTask(**task_data.model_dump())
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def get_scheduled_tasks(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[ScheduledTask]:
        result = await db.execute(select(ScheduledTask).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def get_scheduled_task(db: AsyncSession, task_id: int) -> ScheduledTask | None:
        return await db.get(ScheduledTask, task_id)

    @staticmethod
    async def update_scheduled_task(db: AsyncSession, task_id: int, task_data) -> ScheduledTask | None:
        task = await db.get(ScheduledTask, task_id)
        if task:
            for field, value in task_data.model_dump(exclude_unset=True).items():
                setattr(task, field, value)
            await db.commit()
            await db.refresh(task)
        return task

    @staticmethod
    async def delete_scheduled_task(db: AsyncSession, task_id: int) -> bool:
        task = await db.get(ScheduledTask, task_id)
        if task:
            db.delete(task)
            await db.commit()
            return True
        return False
