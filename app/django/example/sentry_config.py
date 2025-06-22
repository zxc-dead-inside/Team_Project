import logging
import os

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration


logger = logging.getLogger(__name__)


class SentryLoggingFilter:
    """Custom filter to prevent duplicate logging to Sentry"""

    def filter(self, record):
        # Don't send logs that are already handled by Sentry's automatic error capture
        if record.levelno >= logging.ERROR and hasattr(record, "exc_info") and record.exc_info:
            return False
        return True


def setup_sentry():
    """Configure Sentry for Django application"""

    sentry_dsn = os.getenv("SENTRY_DSN")
    sentry_environment = os.getenv("SENTRY_ENVIRONMENT", "local")
    sentry_enable = os.getenv("SENTRY_ENABLE", "false").lower() == "true"
    sentry_release = os.getenv("SENTRY_RELEASE")
    traces_sample_rate = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0"))
    send_default_pii = os.getenv("SENTRY_SEND_DEFAULT_PII", "false").lower() == "true"

    if not sentry_enable or not sentry_dsn:
        logger.info("Sentry is disabled or DSN not configured properly")
        return

    # Configure logging integration
    logging_integration = LoggingIntegration(
        level=logging.INFO,  # Capture info and above as breadcrumbs
        event_level=logging.ERROR,  # Send errors as events
    )

    # Configure Django integration
    django_integration = DjangoIntegration(
        transaction_style="url",
        middleware_spans=True,
        signals_spans=True,
        cache_spans=True,
    )

    # Configure Redis integration
    redis_integration = RedisIntegration()

    try:
        init_kwargs = {
            "dsn": sentry_dsn,
            "environment": sentry_environment,
            "integrations": [
                django_integration,
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

        # Add release if provided
        if sentry_release:
            init_kwargs["release"] = sentry_release

        sentry_sdk.init(**init_kwargs)

        logger.info(f"Sentry initialized successfully for environment: {sentry_environment}")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def before_send_filter(event, hint):
    """Filter events before sending to Sentry"""

    # Don't send events from health check endpoints
    if "request" in event and event["request"].get("url"):
        url = event["request"]["url"]
        if any(path in url for path in ["/health/", "/status/", "/ping/"]):
            return None

    # Don't send certain exception types
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]
        if exc_type.__name__ in ["KeyboardInterrupt", "SystemExit"]:
            return None

    # Add custom context
    event.setdefault("extra", {})
    event["extra"]["service"] = "django"

    return event


def before_send_transaction_filter(event, hint):
    """Filter transactions before sending to Sentry"""

    # Don't track health check transactions
    if event.get("transaction"):
        transaction_name = event["transaction"]
        if any(path in transaction_name for path in ["/health/", "/status/", "/ping/"]):
            return None

    return event


class SentryContextMiddleware:
    """Middleware to add context to Sentry events"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Set user context for Sentry
        with sentry_sdk.configure_scope() as scope:
            if hasattr(request, "user") and request.user.is_authenticated:
                scope.set_user(
                    {
                        "id": request.user.id,
                        "username": getattr(request.user, "username", "Unknown"),
                        "email": getattr(request.user, "email", ""),
                    }
                )

            # Add request context
            scope.set_context(
                "request",
                {
                    "method": request.method,
                    "path": request.path,
                    "query_string": request.META.get("QUERY_STRING", ""),
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                    "remote_addr": request.META.get("REMOTE_ADDR", ""),
                },
            )

            # Add custom tags
            scope.set_tag("service", "django")
            scope.set_tag("environment", os.getenv("SENTRY_ENVIRONMENT", "local"))

        response = self.get_response(request)
        return response


class SentryLogger:
    """Enhanced logger that integrates with Sentry"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, extra=None, **kwargs):
        """Log info with optional Sentry breadcrumb"""
        self.logger.info(message, extra=extra)

        # Add breadcrumb to Sentry
        sentry_sdk.add_breadcrumb(message=message, level="info", data=kwargs)

    def warning(self, message: str, extra=None, **kwargs):
        """Log warning with Sentry breadcrumb"""
        self.logger.warning(message, extra=extra)

        sentry_sdk.add_breadcrumb(message=message, level="warning", data=kwargs)

    def error(self, message: str, error: Exception = None, extra=None, **kwargs):
        """Log error and capture in Sentry"""
        self.logger.error(message, extra=extra, exc_info=error is not None)

        # Capture exception in Sentry with additional context
        with sentry_sdk.configure_scope() as scope:
            for key, value in kwargs.items():
                scope.set_extra(key, value)

            if error:
                sentry_sdk.capture_exception(error)
            else:
                sentry_sdk.capture_message(message, level="error")

    def debug(self, message: str, extra=None, **kwargs):
        """Log debug with Sentry breadcrumb"""
        self.logger.debug(message, extra=extra)

        sentry_sdk.add_breadcrumb(message=message, level="debug", data=kwargs)


def capture_custom_event(event_name: str, **kwargs):
    """Capture custom event in Sentry"""
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("event_type", "custom")
        for key, value in kwargs.items():
            scope.set_extra(key, value)

        sentry_sdk.capture_message(event_name, level="info")


def capture_performance_issue(operation: str, duration: float, threshold: float = 1.0):
    """Capture performance issues"""
    if duration > threshold:
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("performance_issue", True)
            scope.set_extra("operation", operation)
            scope.set_extra("duration", duration)
            scope.set_extra("threshold", threshold)

            sentry_sdk.capture_message(
                f"Performance issue: {operation} took {duration:.2f}s", level="warning"
            )
