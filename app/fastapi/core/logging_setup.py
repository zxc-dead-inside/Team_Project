import json
import logging
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)


def setup_logging():
    """Configure logging for FastAPI application"""

    # Create logs directory
    from pathlib import Path

    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)

    # Create formatters
    json_formatter = JSONFormatter()
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.INFO)

    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "error.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )
    error_handler.setFormatter(json_formatter)
    error_handler.setLevel(logging.ERROR)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)

    # Configure uvicorn loggers
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers = [file_handler, console_handler]

    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = [file_handler, console_handler]


class StructuredLogger:
    """Structured logger for FastAPI application"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, **kwargs):
        extra = {"extra_data": kwargs} if kwargs else {}
        self.logger.info(message, extra=extra)

    def error(self, message: str, error: Exception | None = None, **kwargs):
        extra = {"extra_data": kwargs} if kwargs else {}
        if error:
            extra["extra_data"] = extra.get("extra_data", {})
            extra["extra_data"]["error_type"] = type(error).__name__
            extra["extra_data"]["error_message"] = str(error)
        self.logger.error(message, extra=extra, exc_info=error is not None)

    def warning(self, message: str, **kwargs):
        extra = {"extra_data": kwargs} if kwargs else {}
        self.logger.warning(message, extra=extra)

    def debug(self, message: str, **kwargs):
        extra = {"extra_data": kwargs} if kwargs else {}
        self.logger.debug(message, extra=extra)
