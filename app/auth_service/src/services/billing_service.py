"""Billing service for payment operations."""

from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
from fastapi import HTTPException

from src.core.config import Settings
from src.db.models import (
    TransactionStatus,
    TransactionType,
    User,
)
from src.db.repositories.transaction_repository import (
    SubscriptionRepository,
    TransactionRepository,
)


class BillingService:
    """Service for billing operations."""

    def __init__(
        self,
        settings: Settings,
        transaction_repo: TransactionRepository,
        subscription_repo: SubscriptionRepository,
    ):
        self.settings = settings
        self.transaction_repo = transaction_repo
        self.subscription_repo = subscription_repo

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get HTTP client with configured timeout."""
        return httpx.AsyncClient(timeout=self.settings.http_client_timeout)

    async def create_charge(
        self,
        *,
        user: User,
        subscription_type: str,
        amount: Decimal,
        return_url: str | None = None,
    ) -> dict[str, Any]:
        """Create a charge for subscription."""
        payload = {
            "user_id": str(user.id),
            "subscription_type": subscription_type,
            "amount": str(amount),
            "return_url": return_url,
        }

        async with self._get_http_client() as client:
            try:
                resp = await client.post(
                    f"{self.settings.payment_service_url}/api/v1/payments/charge",
                    json=payload,
                    headers={"X-User-Id": str(user.id)},
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Save failed transaction
                await self.transaction_repo.create_transaction(
                    user_id=user.id,
                    type_=TransactionType.CHARGE,
                    status=TransactionStatus.FAILED,
                    amount=amount,
                    subscription_type=subscription_type,
                    description="Charge failed",
                    error_message=str(e),
                    transaction_metadata={"request": payload},
                )
                raise HTTPException(
                    status_code=e.response.status_code, detail=e.response.text
                )

        payment_data = resp.json()

        # Save successful transaction
        transaction_status = (
            TransactionStatus.PENDING
            if payment_data.get("status") == "pending"
            else TransactionStatus.SUCCEEDED
        )
        
        transaction = await self.transaction_repo.create_transaction(
            user_id=user.id,
            type_=TransactionType.CHARGE,
            status=transaction_status,
            amount=Decimal(str(payment_data.get("amount"))),
            subscription_type=subscription_type,
            description=f"Subscription: {subscription_type}",
            provider_payment_id=payment_data.get("provider_payment_id"),
            transaction_metadata=payment_data,
        )

        # Activate subscription for successful payments
        if transaction.status == TransactionStatus.SUCCEEDED:
            await self.subscription_repo.activate_subscription(
                user.id, transaction.provider_payment_id
            )

        return {
            "provider_payment_id": payment_data.get("provider_payment_id"),
            "status": payment_data.get("status"),
            "amount": Decimal(str(payment_data.get("amount"))),
            "currency": str(payment_data.get("currency")),
            "confirmation_url": payment_data.get("confirmation_url"),
        }

    async def create_refund(
        self,
        *,
        user: User,
        payment_id: str,
        amount: Decimal | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Create a refund for payment."""
        payload = {
            "payment_id": payment_id,
            "amount": str(amount) if amount else None,
            "reason": reason,
        }

        async with self._get_http_client() as client:
            try:
                resp = await client.post(
                    f"{self.settings.payment_service_url}/api/v1/payments/refund",
                    json=payload,
                )
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                # Save failed refund transaction
                await self.transaction_repo.create_transaction(
                    user_id=user.id,
                    type_=TransactionType.REFUND,
                    status=TransactionStatus.FAILED,
                    amount=Decimal("0"),
                    description="Refund failed",
                    provider_payment_id=payment_id,
                    error_message=str(e),
                    transaction_metadata={"request": payload},
                )
                raise HTTPException(
                    status_code=e.response.status_code, detail=e.response.text
                )

        refund_data = resp.json()

        # Save refund transaction
        refund_status = (
            TransactionStatus.REFUNDED
            if refund_data.get("status") in {"refunded", "succeeded"}
            else TransactionStatus.PENDING
        )
        
        transaction = await self.transaction_repo.create_transaction(
            user_id=user.id,
            type_=TransactionType.REFUND,
            status=refund_status,
            amount=Decimal(str(refund_data.get("amount"))),
            description=f"Refund for payment {payment_id}",
            provider_payment_id=payment_id,
            provider_refund_id=refund_data.get("provider_refund_id"),
            transaction_metadata=refund_data,
        )

        return {
            "provider_refund_id": transaction.provider_refund_id or "",
            "status": "refunded" if transaction.status == TransactionStatus.REFUNDED else "pending",
            "amount": transaction.amount,
        }
