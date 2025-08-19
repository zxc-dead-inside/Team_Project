"""Billing endpoints: create charge and refund via payment-service.

Получает пользователя из авторизации, вызывает платежный сервис,
сохраняет результат в БД (Transaction) и при успехе обновляет Subscription.
"""

from decimal import Decimal
from typing import Annotated

import httpx
from pydantic import BaseModel
from src.api.dependencies import get_current_active_user
from src.core.config import get_settings
from src.db.models import (
    Subscription,
    SubscriptionStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)
from src.db.repositories.user_repository import UserRepository

from fastapi import APIRouter, Depends, HTTPException, status


router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])


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


async def _get_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(timeout=10)


@router.post("/charge", response_model=ChargeResponse)
async def create_charge(
    body: ChargeRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    settings = get_settings()

    payload = {
        "user_id": str(current_user.id),
        "subscription_type": body.subscription_type,
        "amount": str(body.amount),
        "return_url": body.return_url,
    }

    async with _get_http_client() as client:
        try:
            resp = await client.post(
                f"{settings.payment_service_url}/api/v1/payments/charge",
                json=payload,
                headers={"X-User-Id": str(current_user.id)},
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            await _save_transaction(
                user_id=current_user.id,
                type_=TransactionType.CHARGE,
                status=TransactionStatus.FAILED,
                amount=body.amount,
                subscription_type=body.subscription_type,
                description="Charge failed",
                error_message=str(e),
                metadata={"request": payload},
            )
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    data = resp.json()

    tx = await _save_transaction(
        user_id=current_user.id,
        type_=TransactionType.CHARGE,
        status=TransactionStatus.PENDING if data.get("status") == "pending" else TransactionStatus.SUCCEEDED,
        amount=Decimal(str(data.get("amount"))),
        subscription_type=body.subscription_type,
        description=f"Subscription: {body.subscription_type}",
        provider_payment_id=data.get("provider_payment_id"),
        metadata=data,
    )

    # Активируем/обновляем подписку при успешной оплате
    if tx.status == TransactionStatus.SUCCEEDED:
        await _activate_subscription(current_user.id, tx.provider_payment_id)

    return ChargeResponse(
        provider_payment_id=data.get("provider_payment_id"),
        status=data.get("status"),
        amount=Decimal(str(data.get("amount"))),
        currency=str(data.get("currency")),
        confirmation_url=data.get("confirmation_url"),
    )


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
    body: RefundRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    settings = get_settings()

    payload = {
        "payment_id": body.payment_id,
        "amount": str(body.amount) if body.amount else None,
        "reason": body.reason,
    }

    async with _get_http_client() as client:
        try:
            resp = await client.post(
                f"{settings.payment_service_url}/api/v1/payments/refund",
                json=payload,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            await _save_transaction(
                user_id=current_user.id,
                type_=TransactionType.REFUND,
                status=TransactionStatus.FAILED,
                amount=Decimal("0"),
                description="Refund failed",
                provider_payment_id=body.payment_id,
                error_message=str(e),
                metadata={"request": payload},
            )
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    data = resp.json()

    tx = await _save_transaction(
        user_id=current_user.id,
        type_=TransactionType.REFUND,
        status=TransactionStatus.REFUNDED if data.get("status") in {"refunded", "succeeded"} else TransactionStatus.PENDING,
        amount=Decimal(str(data.get("amount"))),
        description=f"Refund for payment {body.payment_id}",
        provider_payment_id=body.payment_id,
        provider_refund_id=data.get("provider_refund_id"),
        metadata=data,
    )

    return RefundResponse(
        provider_refund_id=tx.provider_refund_id or "",
        status="refunded" if tx.status == TransactionStatus.REFUNDED else "pending",
        amount=tx.amount,
    )


# --- Helpers (simple session-per-call via UserRepository session_factory) ---
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def _save_transaction(
    *,
    user_id,
    type_: TransactionType,
    status: TransactionStatus,
    amount: Decimal,
    subscription_type: str | None = None,
    description: str | None = None,
    provider_payment_id: str | None = None,
    provider_refund_id: str | None = None,
    error_message: str | None = None,
    metadata: dict | None = None,
) -> Transaction:
    from src.core.container import Container

    container = Container()
    settings = get_settings()
    Container.init_config_from_settings(container, settings)
    db = container.db()

    async with db.session() as session:
        tx = Transaction(
            user_id=user_id,
            type=type_,
            status=status,
            amount=amount,
            subscription_type=subscription_type,
            description=description,
            provider_payment_id=provider_payment_id,
            provider_refund_id=provider_refund_id,
            metadata=metadata,
        )
        session.add(tx)
        await session.flush()
        return tx


async def _activate_subscription(user_id, provider_payment_id: str | None):
    from src.core.container import Container

    container = Container()
    settings = get_settings()
    Container.init_config_from_settings(container, settings)
    db = container.db()

    async with db.session() as session:
        # Найти существующую подписку или создать новую
        result = await session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription is None:
            subscription = Subscription(
                user_id=user_id,
                status=SubscriptionStatus.ACTIVE.value,
                provider_payment_id=provider_payment_id,
            )
            session.add(subscription)
        else:
            subscription.status = SubscriptionStatus.ACTIVE.value
            subscription.provider_payment_id = provider_payment_id
        await session.flush()


