class PaymentProviderError(Exception):
    """Base exception for payment provider errors"""
    pass


class PaymentNotFoundError(PaymentProviderError):
    """Payment not found in provider"""
    pass


class InvalidPaymentStateError(PaymentProviderError):
    """Payment is in invalid state for requested operation"""
    pass


class IdempotencyError(PaymentProviderError):
    """Idempotency key conflict"""
    pass