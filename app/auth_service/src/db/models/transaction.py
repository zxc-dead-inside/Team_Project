import enum

from sqlalchemy import Column, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from src.db.base_models import Base, PreBase


class TransactionType(enum.Enum):
    CHARGE = "CHARGE"
    REFUND = "REFUND"


class TransactionStatus(enum.Enum):
    PENDING = "PENDING"
    SUCCEEDED = "SUCCEEDED"
    CANCELED = "CANCELED"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class Transaction(PreBase, Base):
    __tablename__ = "transaction"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    type = Column(Enum(TransactionType, name="transaction_type"), nullable=False)

    status = Column(Enum(TransactionStatus, name="transaction_status"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)

    currency = Column(String(3), nullable=False, default="RUB")

    subscription_type = Column(String(64), nullable=True)

    description = Column(String(255), nullable=True)

    provider_payment_id = Column(String(128), nullable=True, index=True)

    provider_refund_id = Column(String(128), nullable=True, index=True)

    order_id = Column(String(128), nullable=True)

    error_message = Column(Text, nullable=True)

    metadata = Column(JSONB, nullable=True)

    user = relationship("User")


