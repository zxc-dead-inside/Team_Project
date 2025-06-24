import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from pythonjsonlogger import jsonlogger


class DjangoJSONFormatter(jsonlogger.JsonFormatter):
    """Enhanced JSON formatter for Django with ELK stack integration"""

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record["timestamp"] = datetime.now(UTC).isoformat()

        # Add service identifier
        log_record["service"] = "django"

        # Add request information if available
        if hasattr(record, "request"):
            request = record.request
            log_record["request_data"] = {
                "method": getattr(request, "method", None),
                "path": getattr(request, "path", None),
                "user": str(getattr(request, "user", "Anonymous")),
                "ip": self.get_client_ip(request),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "request_id": request.META.get("HTTP_X_REQUEST_ID", ""),
            }

        # Add user information if available
        if hasattr(record, "user"):
            log_record["user_data"] = {
                "id": getattr(record.user, "id", None),
                "username": getattr(record.user, "username", "Anonymous"),
                "is_authenticated": getattr(record.user, "is_authenticated", False),
            }

        # Add exception details if available
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

    @staticmethod
    def get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


def setup_django_logging():
    """
    Enhanced Django logging configuration for ELK stack.
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)

    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{levelname} {message}",
                "style": "{",
            },
            "json": {
                "()": DjangoJSONFormatter,
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s",
            },
            "elk_json": {
                "()": DjangoJSONFormatter,
                "format": "%(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "level": log_level,
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
            "file": {
                "level": log_level,
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_dir / "django.log"),
                "maxBytes": 1024 * 1024 * 10,  # 10 MB
                "backupCount": 5,
                "formatter": "elk_json",
            },
            "error_file": {
                "level": "ERROR",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_dir / "django_error.log"),
                "maxBytes": 1024 * 1024 * 10,  # 10 MB
                "backupCount": 5,
                "formatter": "elk_json",
            },
            "security_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_dir / "django_security.log"),
                "maxBytes": 1024 * 1024 * 10,  # 10 MB
                "backupCount": 5,
                "formatter": "elk_json",
            },
            "performance_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(log_dir / "django_performance.log"),
                "maxBytes": 1024 * 1024 * 10,  # 10 MB
                "backupCount": 5,
                "formatter": "elk_json",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": log_level,
        },
        "loggers": {
            "django": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "django.request": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": False,
            },
            "django.server": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "django.security": {
                "handlers": ["console", "security_file"],
                "level": log_level,
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["console", "file"],
                "level": "WARNING",  # Reduce DB query logging
                "propagate": False,
            },
            # Your application loggers
            "theatre": {  # Replace with your app name
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "etl": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            # Performance logger
            "performance": {
                "handlers": ["performance_file"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    return logging


# For Django settings.py
LOGGING = setup_django_logging()


class EnhancedStructuredDjangoLogger:
    """
    Enhanced structured logger wrapper for Django applications with ELK integration.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, request=None, user=None, **kwargs):
        """Log info message with structured data"""
        extra = self._build_extra(request=request, user=user, **kwargs)
        self.logger.info(message, extra=extra)

    def error(
        self, message: str, error: Exception = None, request=None, user=None, **kwargs
    ):
        """Log error message with structured data"""
        extra = self._build_extra(request=request, user=user, **kwargs)
        if error:
            extra["error_type"] = type(error).__name__
            extra["error_message"] = str(error)
        self.logger.error(message, extra=extra, exc_info=error is not None)

    def warning(self, message: str, request=None, user=None, **kwargs):
        """Log warning message with structured data"""
        extra = self._build_extra(request=request, user=user, **kwargs)
        self.logger.warning(message, extra=extra)

    def debug(self, message: str, request=None, user=None, **kwargs):
        """Log debug message with structured data"""
        extra = self._build_extra(request=request, user=user, **kwargs)
        self.logger.debug(message, extra=extra)

    def security(self, message: str, request=None, user=None, **kwargs):
        """Log security-related events"""
        security_logger = logging.getLogger("django.security")
        extra = self._build_extra(request=request, user=user, **kwargs)
        extra["security_event"] = True
        security_logger.info(message, extra=extra)

    def performance(self, message: str, duration: float = None, request=None, **kwargs):
        """Log performance metrics"""
        performance_logger = logging.getLogger("performance")
        extra = self._build_extra(request=request, **kwargs)
        if duration:
            extra["duration"] = duration
        extra["performance_event"] = True
        performance_logger.info(message, extra=extra)

    def _build_extra(self, request=None, user=None, **kwargs):
        """Build extra data for logging"""
        extra = {}

        if request:
            extra["request"] = request

        if user:
            extra["user"] = user

        if kwargs:
            extra["structured_data"] = kwargs

        return extra


def get_django_logger(name: str) -> EnhancedStructuredDjangoLogger:
    """
    Get an enhanced structured logger instance for Django.

    Args:
        name: Logger name (usually __name__)

    Returns:
        EnhancedStructuredDjangoLogger instance
    """
    return EnhancedStructuredDjangoLogger(name)


class SecurityEventLogger:
    """Logger for security-related events"""

    def __init__(self):
        self.logger = get_django_logger("django.security")

    def log_login_attempt(self, username: str, success: bool, request=None, **kwargs):
        """Log login attempts"""
        self.logger.security(
            f"Login {'successful' if success else 'failed'}",
            request=request,
            username=username,
            login_success=success,
            **kwargs,
        )

    def log_permission_denied(self, user, resource: str, request=None, **kwargs):
        """Log permission denied events"""
        self.logger.security(
            "Permission denied", request=request, user=user, resource=resource, **kwargs
        )

    def log_suspicious_activity(self, description: str, request=None, **kwargs):
        """Log suspicious activities"""
        self.logger.security(
            f"Suspicious activity: {description}", request=request, **kwargs
        )
