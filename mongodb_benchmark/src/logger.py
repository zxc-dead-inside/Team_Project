import logging
from pathlib import Path
from datetime import datetime

def setup_logging(log_dir: str = "logs", log_level: int = logging.INFO) -> None:
    """
    Настройка системы логирования
    
    :param log_dir: Директория для хранения логов
    :param log_level: Уровень логирования (по умолчанию: INFO)
    """
    # Создаем директорию для логов, если ее нет
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Генерируем имя файла с текущей датой и временем
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"{log_dir}/app_{timestamp}.log"
    
    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    # Настройка root логгера
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Очистка предыдущих обработчиков
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Файловый обработчик
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
       
    # Информационное сообщение о начале работы
    logger.info("=" * 50)
    logger.info(f"Logging initialized. Log file: {log_filename}")
    logger.info("=" * 50)