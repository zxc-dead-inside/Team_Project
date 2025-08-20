# from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from app.core.abstractions import PaymentResponse, RefundResponse
from app.core.exceptions import InvalidPaymentStateError, PaymentNotFoundError, PaymentProviderError
from app.services.payment_service import PaymentService
from app.core.models import CreatePaymentRequest, CreateRefundRequest


router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


# Dependency injection for payment service
async def get_payment_service() -> PaymentService:
    from app.main import payment_service
    return payment_service


@router.post("/charge", response_model=PaymentResponse)
async def create_payment(
    request: CreatePaymentRequest,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    x_user_id: str | None = Header(None, description="User ID from auth service")
):
    """Create a new payment for subscription"""
    
    # !!! Use header user_id if provided (from auth service), otherwise use request
    user_id = x_user_id or request.user_id
    
    try:
        payment = await service.create_subscription_payment(
            user_id=user_id,
            subscription_type=request.subscription_type,
            amount=float(request.amount),
            return_url=request.return_url
        )
        return payment
    except PaymentProviderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/refund", response_model=RefundResponse)
async def create_refund(
    request: CreateRefundRequest,
    service: Annotated[PaymentService, Depends(get_payment_service)]
):
    """Create a refund for a payment"""
    
    try:
        refund = await service.process_refund(
            payment_id=request.payment_id,
            amount=float(request.amount) if request.amount else None,
            reason=request.reason
        )
        return refund
    except (PaymentNotFoundError, InvalidPaymentStateError, PaymentProviderError) as e:
        status_code = 404 if isinstance(e, PaymentNotFoundError) else 400
        raise HTTPException(status_code=status_code, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/status/{payment_id}", response_model=PaymentResponse)
async def get_payment_status(
    payment_id: str,
    service: Annotated[PaymentService, Depends(get_payment_service)]
):
    """Get payment status"""
    
    try:
        status = await service.check_payment_status(payment_id)
        return status
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except PaymentProviderError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "payment-service"}