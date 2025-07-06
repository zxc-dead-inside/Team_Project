from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class DeliveryMethod(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"

class MessageStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"

class MessageTemplate(Base):
    __tablename__ = "message_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    delivery_method = Column(Enum(DeliveryMethod), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    messages = relationship("Message", back_populates="template")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    delivery_method = Column(Enum(DeliveryMethod), nullable=False)
    status = Column(Enum(MessageStatus), default=MessageStatus.PENDING)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    template_id = Column(
        Integer, ForeignKey("message_templates.id"), nullable=True
    )
    template = relationship("MessageTemplate", back_populates="messages")
    scheduled_task_id = Column(
        Integer, ForeignKey("scheduled_tasks.id"), nullable=True
    )
    scheduled_task = relationship("ScheduledTask", back_populates="messages")

class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    template_id = Column(
        Integer, ForeignKey("message_templates.id"), nullable=True
    )
    recipients = Column(Text, nullable=False)
    delivery_method = Column(Enum(DeliveryMethod), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    is_recurring = Column(Boolean, default=False)
    cron_expression = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    messages = relationship("Message", back_populates="scheduled_task") 