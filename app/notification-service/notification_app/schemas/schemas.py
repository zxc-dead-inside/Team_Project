from datetime import datetime

from pydantic import BaseModel
from notification_app.models.models import DeliveryMethod, MessageStatus


class MessageTemplateBase(BaseModel):
    name: str
    subject: str | None = None
    content: str
    delivery_method: DeliveryMethod


class MessageTemplateCreate(MessageTemplateBase):
    pass


class MessageTemplateUpdate(BaseModel):
    name: str | None = None
    subject: str | None = None
    content: str | None = None
    delivery_method: DeliveryMethod | None = None


class MessageTemplate(MessageTemplateBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class MessageBase(BaseModel):
    recipient: str
    subject: str | None = None
    content: str
    delivery_method: DeliveryMethod


class MessageCreate(MessageBase):
    template_id: int | None = None


class Message(MessageBase):
    id: int
    status: MessageStatus
    sent_at: datetime | None = None
    created_at: datetime
    template_id: int | None = None

    model_config = {"from_attributes": True}


class ScheduledTaskBase(BaseModel):
    name: str
    template_id: int | None = None
    recipients: str
    delivery_method: DeliveryMethod
    scheduled_at: datetime
    is_recurring: bool = False
    cron_expression: str | None = None


class ScheduledTaskCreate(ScheduledTaskBase):
    pass


class ScheduledTaskUpdate(BaseModel):
    name: str | None = None
    template_id: int | None = None
    recipients: str | None = None
    delivery_method: DeliveryMethod | None = None
    scheduled_at: datetime | None = None
    is_recurring: bool | None = None
    cron_expression: str | None = None
    is_active: bool | None = None


class ScheduledTask(ScheduledTaskBase):
    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
