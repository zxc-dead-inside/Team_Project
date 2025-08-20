import enum

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship

from src.db.base_models import Base, PreBase


class SubscriptionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    CANCELED = "CANCELED"


class Subscription(PreBase, Base):
    __tablename__ = "subscription"

    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    status = Column(
        ENUM("ACTIVE", "CANCELED", name="subscription_status"),
        default=SubscriptionStatus.ACTIVE.value,
        nullable=False
    )
    provider_payment_id = Column(String(128), nullable=True)
    canceled_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="subscriptions")