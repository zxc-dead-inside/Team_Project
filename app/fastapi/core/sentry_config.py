import logging
import os
import time

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi import HTTPException, Request

from core.config import settings

logger = logging.getLogger(__name__)


def setup_sentry():
    """Configure Sentry for FastAPI application"""
    
    sentry_dsn = settings.sentry_dsn
    sentry_environment = settings.sentry_environment
    sentry_enable = settings.sentry_enable.lower() == "true"
    traces_sample_rate = settings.sentry_traces_sample_rate
    send_default_pii = settings.sentry_send_default_pii.lower() == "true"
    
    if not sentry_enable or not sentry_dsn:
        logger.info("Sentry is disabled or DSN not configured properly")
        return
    
    # Configure logging integration - ERROR LEVEL ONLY
    logging_integration = LoggingIntegration(
        level=logging.WARNING,
        event_level=logging.ERROR
    )
    
    # Configure FastAPI integration
    fastapi_integration = FastApiIntegration(
        transaction_style="endpoint",
    )
    
    # Configure Starlette integration
    starlette_integration = StarletteIntegration(
        transaction_style="endpoint",
        failed_request_status_codes=[500, 502, 503, 504],
    )
    
    # Configure Redis integration
    redis_integration = RedisIntegration()
    
    try:
        init_kwargs = {
            "dsn": sentry_dsn,
            "environment": sentry_environment,
            "integrations": [
                fastapi_integration,
                starlette_integration,
                logging_integration,
                redis_integration,
            ],
            "traces_sample_rate": traces_sample_rate,
            "send_default_pii": send_default_pii,
            "debug": os.getenv("DEBUG", "false").lower() == "true",
            "attach_stacktrace": True,
            "before_send": before_send_filter,
            "before_send_transaction": before_send_transaction_filter,
        }
        
        sentry_sdk.init(**init_kwargs)
        
        logger.info(f"Sentry initialized successfully for environment: {sentry_environment}")
        
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """Filter events before sending to Sentry"""
    
    # Don't send events from health check endpoints
    if 'request' in event and event['request'].get('url'):
        url = event['request']['url']
        if any(path in url for path in ['/health', '/docs', '/redoc', '/openapi.json']):
            return None
    
    # Don't send certain exception types
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if exc_type.__name__ in ['KeyboardInterrupt', 'SystemExit']:
            return None
        
        # Don't send HTTP 404 errors
        if isinstance(exc_value, HTTPException) and exc_value.status_code == 404:
            return None
    
    # Add custom context
    event.setdefault('extra', {})
    event['extra']['service'] = 'fastapi'
    
    return event


def before_send_transaction_filter(event, hint):
    """Filter transactions before sending to Sentry"""
    
    # Don't track health check transactions
    if event.get('transaction'):
        transaction_name = event['transaction']
        if any(path in transaction_name for path in ['/health', '/docs', '/redoc', '/openapi.json']):
            return None
    
    return event


class SentryContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add context to Sentry events"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Set request context for Sentry
        with sentry_sdk.configure_scope() as scope:
            # Add request context
            scope.set_context("request", {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_string": str(request.url.query),
                "headers": dict(request.headers),
                "client_host": request.client.host if request.client else None,
            })
            
            # Add custom tags
            scope.set_tag("service", "fastapi")
            scope.set_tag("environment", os.getenv("SENTRY_ENVIRONMENT", "local"))
            
            # Add user context if available (from JWT or auth)
            if hasattr(request.state, 'user') and request.state.user:
                scope.set_user({
                    "id": getattr(request.state.user, 'id', None),
                    "username": getattr(request.state.user, 'username', 'Unknown'),
                    "email": getattr(request.state.user, 'email', ''),
                })
        
        try:
            response = await call_next(request)
            
            # Add response context
            duration = time.time() - start_time
            with sentry_sdk.configure_scope() as scope:
                scope.set_context("response", {
                    "status_code": response.status_code,
                    "duration": duration,
                })
            
            return response
            
        except Exception as e:
            # Capture exception with context
            duration = time.time() - start_time
            with sentry_sdk.configure_scope() as scope:
                scope.set_extra("request_duration", duration)
                scope.set_extra("error_during_request", True)
            
            sentry_sdk.capture_exception(e)
            raise


class SentryStructuredLogger:
    """Enhanced structured logger that integrates with Sentry"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log info with Sentry breadcrumb"""
        extra = {"extra_data": kwargs} if kwargs else {}
        self.logger.info(message, extra=extra)
        
        # Add breadcrumb to Sentry
        sentry_sdk.add_breadcrumb(
            message=message,
            level='info',
            data=kwargs
        )
    
    def warning(self, message: str, **kwargs):
        """Log warning with Sentry breadcrumb"""
        extra = {"extra_data": kwargs} if kwargs else {}
        self.logger.warning(message, extra=extra)
        
        sentry_sdk.add_breadcrumb(
            message=message,
            level='warning',
            data=kwargs
        )
    
    def error(self, message: str, error: Exception | None = None, **kwargs):
        """Log error and capture in Sentry"""
        extra = {"extra_data": kwargs} if kwargs else {}
        if error:
            extra["extra_data"] = extra.get("extra_data", {})
            extra["extra_data"]["error_type"] = type(error).__name__
            extra["extra_data"]["error_message"] = str(error)
        
        self.logger.error(message, extra=extra, exc_info=error is not None)
        
        # Capture in Sentry with additional context
        with sentry_sdk.configure_scope() as scope:
            for key, value in kwargs.items():
                scope.set_extra(key, value)
            
            if error:
                sentry_sdk.capture_exception(error)
            else:
                sentry_sdk.capture_message(message, level='error')
    
    def debug(self, message: str, **kwargs):
        """Log debug with Sentry breadcrumb"""
        extra = {"extra_data": kwargs} if kwargs else {}
        self.logger.debug(message, extra=extra)
        
        sentry_sdk.add_breadcrumb(
            message=message,
            level='debug',
            data=kwargs
        )


def capture_api_error(endpoint: str, error: Exception, request_data: dict = None):
    """Capture API-specific errors"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("api_error", True)
        scope.set_extra("endpoint", endpoint)
        if request_data:
            scope.set_extra("request_data", request_data)
        
        sentry_sdk.capture_exception(error)


def capture_performance_issue(operation: str, duration: float, threshold: float = 1.0):
    """Capture performance issues"""
    if duration > threshold:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("performance_issue", True)
            scope.set_extra("operation", operation)
            scope.set_extra("duration", duration)
            scope.set_extra("threshold", threshold)
            
            sentry_sdk.capture_message(
                f"Performance issue: {operation} took {duration:.2f}s",
                level='warning'
            )


def capture_business_event(event_name: str, **kwargs):
    """Capture business logic events"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("business_event", True)
        scope.set_tag("event_name", event_name)
        for key, value in kwargs.items():
            scope.set_extra(key, value)
        
        sentry_sdk.capture_message(event_name, level='info')