import enum

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class DeliveryMethod(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


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
