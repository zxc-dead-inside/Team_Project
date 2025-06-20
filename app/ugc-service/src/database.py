from motor.motor_asyncio import AsyncIOMotorClient
from .config import settings


class Database:
    client: AsyncIOMotorClient = None
    database = None


db = Database()


async def connect_to_mongo():
    """Подключение к MongoDB"""
    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.database = db.client[settings.mongodb_database]
    print("Connected to MongoDB")


async def close_mongo_connection():
    """Закрытие соединения с MongoDB"""
    if db.client:
        db.client.close()
        print("Disconnected from MongoDB")


def get_database():
    """Получение экземпляра базы данных"""
    return db.database 