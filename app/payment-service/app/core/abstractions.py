from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: Currency = Currency.RUB
    description: str
    user_id: str
    order_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    return_url: str | None = None


class RefundRequest(BaseModel):
    payment_id: str
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    reason: str | None = None


class PaymentResponse(BaseModel):
    provider_payment_id: str
    status: PaymentStatus
    amount: Decimal
    currency: Currency
    created_at: datetime
    confirmation_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RefundResponse(BaseModel):
    provider_refund_id: str
    payment_id: str
    status: PaymentStatus
    amount: Decimal
    created_at: datetime


class PaymentProvider(ABC):
    """Abstract base class for payment providers"""
    
    @abstractmethod
    async def charge(
        self, 
        request: PaymentRequest,
        idempotence_key: str | None = None
    ) -> PaymentResponse:
        """Create a payment charge"""
        pass
    
    @abstractmethod
    async def refund(
        self,
        request: RefundRequest,
        idempotence_key: str | None = None
    ) -> RefundResponse:
        """Refund a payment"""
        pass
    
    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> PaymentResponse:
        """Check payment status"""
        pass
