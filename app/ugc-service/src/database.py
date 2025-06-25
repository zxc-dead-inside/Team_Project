from motor.motor_asyncio import AsyncIOMotorClient
from src.config import settings
from src.logger_setup import logger

class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def connect_to_mongo():
    """Подключение к MongoDB"""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.mongodb_database]
    logger.info("Connected to MongoDB")


async def close_mongo_connection():
    """Закрытие соединения с MongoDB"""
    if db.client:
        db.client.close()
        logger.info("Disconnected from MongoDB")


def get_database():
    """Получение экземпляра базы данных"""
    return db.database 