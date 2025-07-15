import logging
import sys
from pathlib import Path

from loguru import logger


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru."""

    def emit(self, record):
        """Emit a log record."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_level: str = "INFO"):
    """Configure logging for the application."""
    # Set log level for root logger
    logging.root.setLevel(log_level)

    # Remove default handlers and add InterceptHandler
    logging.root.handlers = [InterceptHandler()]

    # Set log levels for libraries
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    # Configure loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "level": log_level,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            }
        ]
    )

    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Add file handler for non-development environments
    logger.add(
        "logs/auth_service.log",
        rotation="10 MB",
        retention="1 week",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    )



# import logging
# import sys
# import json
# from logging import config as logging_config

# LOGGING_CONFIG = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "json": {
#             "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
#             "format": "%(asctime)s %(levelname)s %(name)s %(message)s"
#         },
#         "simple": {
#             "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
#         }
#     },
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#             "formatter": "simple",
#             "stream": sys.stdout
#         },
#         "json_console": {
#             "class": "logging.StreamHandler",
#             "formatter": "json",
#             "stream": sys.stdout
#         }
#     },
#     "loggers": {
#         "": {
#             "handlers": ["console"],
#             "level": "INFO",
#             "propagate": True
#         },
#         "src": {
#             "handlers": ["json_console"],
#             "level": "DEBUG",
#             "propagate": False
#         },
#         "uvicorn": {
#             "handlers": ["console"],
#             "level": "INFO",
#             "propagate": False
#         },
#         "uvicorn.error": {
#             "level": "INFO",
#             "propagate": False
#         }
#     }
# }

# def setup_logging():
#     """Настройка системы логирования"""
#     logging_config.dictConfig(LOGGING_CONFIG)
#     logging.captureWarnings(True)
#     logging.getLogger("aiokafka").setLevel(logging.WARNING)
#     logging.getLogger("asyncio").setLevel(logging.INFO)