from datetime import UTC, datetime
from fastapi import Request

from core.logging_setup import StructuredLogger

logger = StructuredLogger(__name__)


async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = datetime.now(UTC)

    # Log request
    logger.info(
        "HTTP request received",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
        request_id=request.headers.get("x-request-id"),
    )

    try:
        response = await call_next(request)

        # Calculate processing time
        process_time = (datetime.now(UTC) - start_time).total_seconds()

        # Log response
        logger.info(
            "HTTP request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            request_id=request.headers.get("x-request-id"),
        )

        return response

    except Exception as e:
        process_time = (datetime.now(UTC) - start_time).total_seconds()
        logger.error(
            "HTTP request failed",
            error=e,
            method=request.method,
            url=str(request.url),
            process_time=process_time,
            request_id=request.headers.get("x-request-id"),
        )
        raise