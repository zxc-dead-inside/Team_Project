import logging
import uuid

from app.core.abstractions import (
    PaymentProvider,
    PaymentRequest,
    PaymentResponse,
    RefundRequest,
    RefundResponse,
)
from app.core.exceptions import PaymentProviderError


logger = logging.getLogger(__name__)


class PaymentService:
    """Business logic layer for payments"""
    
    def __init__(self, provider: PaymentProvider):
        self.provider = provider
    
    async def create_subscription_payment(
        self,
        user_id: str,
        subscription_type: str,
        amount: float,
        return_url: str | None = None
    ) -> PaymentResponse:
        """Create a payment for subscription"""
        
        order_id = f"sub_{user_id}_{uuid.uuid4().hex[:8]}"
        
        request = PaymentRequest(
            amount=amount,
            description=f"Subscription: {subscription_type}",
            user_id=user_id,
            order_id=order_id,
            metadata={
                "subscription_type": subscription_type,
                "service": "online_cinema"
            },
            return_url=return_url
        )
        
        idempotence_key = f"payment_{order_id}"
        
        try:
            return await self.provider.charge(request, idempotence_key)
        except PaymentProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_subscription_payment: {e}")
            raise PaymentProviderError(f"Payment creation failed: {str(e)}") from e
    
    async def process_refund(
        self,
        payment_id: str,
        amount: float | None = None,
        reason: str | None = None
    ) -> RefundResponse:
        """Process a refund"""
        
        request = RefundRequest(
            payment_id=payment_id,
            amount=amount,
            reason=reason
        )
        
        idempotence_key = f"refund_{payment_id}_{uuid.uuid4().hex[:8]}"
        
        try:
            return await self.provider.refund(request, idempotence_key)
        except PaymentProviderError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in process_refund: {e}")
            raise PaymentProviderError(f"Refund processing failed: {str(e)}") from e
    
    async def check_payment_status(self, payment_id: str) -> PaymentResponse:
        """Check payment status"""
        return await self.provider.get_payment_status(payment_id)