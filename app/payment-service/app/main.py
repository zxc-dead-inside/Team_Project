import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import router
from app.config import settings
from app.providers.yookassa_provider import YooKassaProvider
from app.services.payment_service import PaymentService


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

payment_service: PaymentService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global payment_service

    if settings.payment_provider == "yookassa":
        provider = YooKassaProvider(
            shop_id=settings.yookassa_shop_id, secret_key=settings.yookassa_secret_key
        )
    else:
        # Here we can add other providers
        raise ValueError(f"Unknown payment provider: {settings.payment_provider}")

    payment_service = PaymentService(provider)
    logger.info(f"Payment service initialized with provider: {settings.payment_provider}")

    yield

    logger.info("Shutting down payment service")


app = FastAPI(
    title="Payment Service",
    description="Payment service for online cinema",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"service": "Payment Service", "version": "1.0.0", "provider": settings.payment_provider}
