import logging
import uuid
from datetime import datetime
from decimal import Decimal

from yookassa import Configuration, Payment, Refund

from app.core.abstractions import (
    Currency,
    PaymentProvider,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    RefundRequest,
    RefundResponse,
)
from app.core.exceptions import InvalidPaymentStateError, PaymentNotFoundError, PaymentProviderError


logger = logging.getLogger(__name__)


class YooKassaProvider(PaymentProvider):
    """YooKassa payment provider adapter"""

    STATUS_MAPPING = {
        "pending": PaymentStatus.PENDING,
        "waiting_for_capture": PaymentStatus.PENDING,
        "succeeded": PaymentStatus.SUCCEEDED,
        "canceled": PaymentStatus.CANCELED,
    }

    # Direct string mapping for currencies
    CURRENCY_MAPPING = {
        Currency.RUB: "RUB",
        Currency.USD: "USD",
        Currency.EUR: "EUR",
    }

    def __init__(self, shop_id: str, secret_key: str):
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        self.shop_id = shop_id

    async def charge(
        self, request: PaymentRequest, idempotence_key: str | None = None
    ) -> PaymentResponse:
        """Create a payment in YooKassa"""

        idempotence_key = idempotence_key or str(uuid.uuid4())

        try:
            payment_data = {
                "amount": {
                    "value": str(request.amount),
                    "currency": self.CURRENCY_MAPPING[request.currency],
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": request.return_url or "https://example.com/return",
                },
                "capture": True,
                "description": request.description,
                "metadata": {
                    **request.metadata,
                    "user_id": request.user_id,
                    "order_id": request.order_id,
                },
            }

            payment = Payment.create(payment_data, idempotence_key)

            return PaymentResponse(
                provider_payment_id=payment.id,
                status=self.STATUS_MAPPING.get(payment.status, PaymentStatus.PENDING),
                amount=Decimal(payment.amount.value),
                currency=request.currency,
                created_at=datetime.fromisoformat(payment.created_at),
                confirmation_url=payment.confirmation.confirmation_url
                if payment.confirmation
                else None,
                metadata=payment.metadata or {},
            )

        except Exception as e:
            logger.error(f"YooKassa charge error: {e}")
            raise PaymentProviderError(f"Failed to create payment: {str(e)}") from e

    async def refund(
        self, request: RefundRequest, idempotence_key: str | None = None
    ) -> RefundResponse:
        """Create a refund in YooKassa"""

        idempotence_key = idempotence_key or str(uuid.uuid4())

        try:
            payment = Payment.find_one(request.payment_id)
            if not payment:
                raise PaymentNotFoundError(f"Payment {request.payment_id} not found")

            if payment.status != "succeeded":
                raise InvalidPaymentStateError(f"Cannot refund payment in status: {payment.status}")

            refund_data = {
                "payment_id": request.payment_id,
                "amount": {
                    "value": str(request.amount) if request.amount else payment.amount.value,
                    "currency": payment.amount.currency,
                },
            }

            if request.reason:
                refund_data["description"] = request.reason

            refund = Refund.create(refund_data, idempotence_key)

            return RefundResponse(
                provider_refund_id=refund.id,
                payment_id=request.payment_id,
                status=PaymentStatus.REFUNDED
                if refund.status == "succeeded"
                else PaymentStatus.PENDING,
                amount=Decimal(refund.amount.value),
                created_at=datetime.fromisoformat(refund.created_at),
            )

        except PaymentNotFoundError:
            raise
        except InvalidPaymentStateError:
            raise
        except Exception as e:
            logger.error(f"YooKassa refund error: {e}")
            raise PaymentProviderError(f"Failed to create refund: {str(e)}") from e

    async def get_payment_status(self, payment_id: str) -> PaymentResponse:
        """Get payment status from YooKassa"""

        try:
            payment = Payment.find_one(payment_id)
            if not payment:
                raise PaymentNotFoundError(f"Payment {payment_id} not found")

            currency_map = {"RUB": Currency.RUB, "USD": Currency.USD, "EUR": Currency.EUR}
            currency = currency_map.get(payment.amount.currency, Currency.RUB)

            return PaymentResponse(
                provider_payment_id=payment.id,
                status=self.STATUS_MAPPING.get(payment.status, PaymentStatus.PENDING),
                amount=Decimal(payment.amount.value),
                currency=currency,
                created_at=datetime.fromisoformat(payment.created_at),
                confirmation_url=getattr(payment.confirmation, "confirmation_url", None)
                if payment.confirmation
                else None,
                metadata=payment.metadata or {},
            )

        except Exception as e:
            logger.error(f"YooKassa get status error: {e}")
            raise PaymentProviderError(f"Failed to get payment status: {str(e)}") from e
