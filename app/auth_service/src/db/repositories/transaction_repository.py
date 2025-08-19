"""Repository for Transaction and Subscription operations."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    Subscription,
    SubscriptionStatus,
    Transaction,
    TransactionStatus,
    TransactionType,
)


class TransactionRepository:
    """Repository for Transaction operations."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def create_transaction(
        self,
        *,
        user_id: UUID,
        type_: TransactionType,
        status: TransactionStatus,
        amount: Decimal,
        subscription_type: str | None = None,
        description: str | None = None,
        provider_payment_id: str | None = None,
        provider_refund_id: str | None = None,
        error_message: str | None = None,
        transaction_metadata: dict | None = None,
    ) -> Transaction:
        """Create a new transaction."""
        async with self.session_factory() as session:
            transaction = Transaction(
                user_id=user_id,
                type=type_,
                status=status,
                amount=amount,
                subscription_type=subscription_type,
                description=description,
                provider_payment_id=provider_payment_id,
                provider_refund_id=provider_refund_id,
                error_message=error_message,
                transaction_metadata=transaction_metadata,
            )
            session.add(transaction)
            await session.flush()
            await session.refresh(transaction)
            return transaction

    async def get_transaction_by_provider_payment_id(
        self, provider_payment_id: str
    ) -> Optional[Transaction]:
        """Get transaction by provider payment ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Transaction).where(
                    Transaction.provider_payment_id == provider_payment_id
                )
            )
            return result.scalar_one_or_none()

    async def get_user_transactions(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Transaction]:
        """Get user transactions with pagination."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Transaction)
                .where(Transaction.user_id == user_id)
                .order_by(Transaction.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())


class SubscriptionRepository:
    """Repository for Subscription operations."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_user_subscription(self, user_id: UUID) -> Optional[Subscription]:
        """Get user subscription."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            return result.scalar_one_or_none()

    async def create_subscription(
        self,
        *,
        user_id: UUID,
        status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
        provider_payment_id: str | None = None,
    ) -> Subscription:
        """Create a new subscription."""
        async with self.session_factory() as session:
            subscription = Subscription(
                user_id=user_id,
                status=status.value,
                provider_payment_id=provider_payment_id,
            )
            session.add(subscription)
            await session.flush()
            await session.refresh(subscription)
            return subscription

    async def update_subscription(
        self,
        subscription: Subscription,
        *,
        status: SubscriptionStatus | None = None,
        provider_payment_id: str | None = None,
    ) -> Subscription:
        """Update subscription."""
        async with self.session_factory() as session:
            # Merge the subscription into the current session
            subscription = await session.merge(subscription)
            
            if status is not None:
                subscription.status = status.value
            if provider_payment_id is not None:
                subscription.provider_payment_id = provider_payment_id
            
            await session.flush()
            await session.refresh(subscription)
            return subscription

    async def activate_subscription(
        self, user_id: UUID, provider_payment_id: str | None = None
    ) -> Subscription:
        """Activate user subscription or create new one."""
        subscription = await self.get_user_subscription(user_id)
        
        if subscription is None:
            return await self.create_subscription(
                user_id=user_id,
                status=SubscriptionStatus.ACTIVE,
                provider_payment_id=provider_payment_id,
            )
        else:
            return await self.update_subscription(
                subscription,
                status=SubscriptionStatus.ACTIVE,
                provider_payment_id=provider_payment_id,
            )
