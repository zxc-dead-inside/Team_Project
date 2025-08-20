from decimal import Decimal

from pydantic import BaseModel, Field


class CreatePaymentRequest(BaseModel):
    user_id: str
    subscription_type: str = Field(..., description="Type of subscription")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    return_url: str | None = Field(None, description="URL to return after payment")


class CreateRefundRequest(BaseModel):
    payment_id: str
    amount: Decimal | None = Field(None, gt=0, decimal_places=2)
    reason: str | None = None
