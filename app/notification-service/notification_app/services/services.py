import logging
from datetime import datetime

from sqlalchemy.orm import Session

from notification_app.models.models import (Message, MessageStatus,
                                            MessageTemplate, ScheduledTask)
from notification_app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class MessageTemplateService:
    @staticmethod
    def create_template(db: Session, template_data) -> MessageTemplate:
        template = MessageTemplate(**template_data.model_dump())
        db.add(template)
        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def get_templates(db: Session, skip: int = 0, limit: int = 100) -> list[MessageTemplate]:
        return db.query(MessageTemplate).offset(skip).limit(limit).all()

    @staticmethod
    def get_template(db: Session, template_id: int) -> MessageTemplate | None:
        return db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()

    @staticmethod
    def update_template(db: Session, template_id: int, template_data) -> MessageTemplate | None:
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if template:
            for field, value in template_data.model_dump(exclude_unset=True).items():
                setattr(template, field, value)
            db.commit()
            db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        template = db.query(MessageTemplate).filter(MessageTemplate.id == template_id).first()
        if template:
            db.delete(template)
            db.commit()
            return True
        return False


class MessageService:
    @staticmethod
    def create_message(db: Session, message_data) -> Message:
        message = Message(**message_data.model_dump())
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def send_message_immediately(db: Session, message: Message) -> bool:
        success = NotificationService.send_message(
            message.recipient, message.subject, message.content, message.delivery_method
        )
        if success:
            message.status = MessageStatus.SENT
            message.sent_at = datetime.utcnow()
        else:
            message.status = MessageStatus.FAILED
        db.commit()
        return success

    @staticmethod
    def get_messages(db: Session, skip: int = 0, limit: int = 100) -> list[Message]:
        return db.query(Message).offset(skip).limit(limit).all()

    @staticmethod
    def get_message(db: Session, message_id: int) -> Message | None:
        return db.query(Message).filter(Message.id == message_id).first()


class ScheduledTaskService:
    @staticmethod
    def create_scheduled_task(db: Session, task_data) -> ScheduledTask:
        task = ScheduledTask(**task_data.model_dump())
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_scheduled_tasks(db: Session, skip: int = 0, limit: int = 100) -> list[ScheduledTask]:
        return db.query(ScheduledTask).offset(skip).limit(limit).all()

    @staticmethod
    def get_scheduled_task(db: Session, task_id: int) -> ScheduledTask | None:
        return db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()

    @staticmethod
    def update_scheduled_task(db: Session, task_id: int, task_data) -> ScheduledTask | None:
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            for field, value in task_data.model_dump(exclude_unset=True).items():
                setattr(task, field, value)
            db.commit()
            db.refresh(task)
        return task

    @staticmethod
    def delete_scheduled_task(db: Session, task_id: int) -> bool:
        task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()
        if task:
            db.delete(task)
            db.commit()
            return True
        return False
