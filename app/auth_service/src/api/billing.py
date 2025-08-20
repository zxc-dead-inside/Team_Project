"""Billing endpoints: create charge and refund via payment-service.

Получает пользователя из авторизации, вызывает платежный сервис,
сохраняет результат в БД (Transaction) и при успехе обновляет Subscription.
"""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel
from fastapi import APIRouter, Depends, Request

from src.api.dependencies import get_current_active_user
from src.db.models import User
from src.services.billing_service import BillingService


router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])


def get_billing_service(request: Request) -> BillingService:
    """Get billing service from container."""
    return request.app.container.billing_service()


class ChargeRequest(BaseModel):
    subscription_type: str
    amount: Decimal
    return_url: str | None = None


class ChargeResponse(BaseModel):
    provider_payment_id: str
    status: str
    amount: Decimal
    currency: str
    confirmation_url: str | None = None


class RefundRequest(BaseModel):
    payment_id: str
    amount: Decimal | None = None
    reason: str | None = None


class RefundResponse(BaseModel):
    provider_refund_id: str
    status: str
    amount: Decimal


@router.post("/charge", response_model=ChargeResponse)
async def create_charge(
    body: ChargeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
):
    """Create a charge for subscription."""
    result = await billing_service.create_charge(
        user=current_user,
        subscription_type=body.subscription_type,
        amount=body.amount,
        return_url=body.return_url,
    )
    
    return ChargeResponse(
        provider_payment_id=result["provider_payment_id"],
        status=result["status"],
        amount=result["amount"],
        currency=result["currency"],
        confirmation_url=result["confirmation_url"],
    )


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
    body: RefundRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    billing_service: Annotated[BillingService, Depends(get_billing_service)],
):
    """Create a refund for payment."""
    result = await billing_service.create_refund(
        user=current_user,
        payment_id=body.payment_id,
        amount=body.amount,
        reason=body.reason,
    )
    
    return RefundResponse(
        provider_refund_id=result["provider_refund_id"],
        status=result["status"],
        amount=result["amount"],
    )

