import os
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import json


def init_logger(service_name: str) -> logging.Logger:
    log_directory = 'logs'
    os.makedirs(log_directory, exist_ok=True)

    log_file = os.path.join(log_directory, 'template_worker.log')

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 10,
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)

    formatter = json.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(module)s %(message)s',
        rename_fields={
            'asctime': '@timestamp',
            'levelname': 'log.level',
        },
        timestamp='@timestamp'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


logger = init_logger('template_worker')
