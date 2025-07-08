from typing import Literal

from pydantic import BaseModel


class IncomingEvent(BaseModel):
    user_id: int
    template_id: int | None = None
    subject: str | None = None
    text: str
    delivery_method: Literal["email", "sms", "push"]


class FixedEvent(BaseModel):
    type: str
    data: dict


class BroadcastMessage(BaseModel):
    template_id: int
    subject: str | None = None
    content: str


class PersonalizedMessage(BaseModel):
    user_id: int
    template_id: int
    subject: str | None = None
    content: str


class PersonalizedBatch(BaseModel):
    messages: list[PersonalizedMessage]
