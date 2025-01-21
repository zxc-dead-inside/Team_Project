import logging


def setup_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler('app.log')
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    return logger
