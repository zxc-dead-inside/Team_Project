import asyncio
import json
import logging
from collections import defaultdict

from fastapi import HTTPException, WebSocket, status

from src.core.logger import setup_logging
from src.services.redis import RedisService

setup_logging()


class ConnectionManager:
    def __init__(self,  redis_service: RedisService):
        self.active_connections = defaultdict(dict[str, WebSocket])
        self.redis_service = redis_service
        
    async def connect(self, user_id: str, websocket: WebSocket):
        """Регистрация нового соединения"""

        await websocket.accept()
        
        self.active_connections[user_id] = websocket
        
        connection_info = {
            "user_id": user_id,
            "client": f"{websocket.client.host}:{websocket.client.port}"
        }
        
        result = await self.redis_service.hset(
            "active_connections", 
            user_id, 
            json.dumps(connection_info)
        )
        if not result:
            raise HTTPException (
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error with redis.")
        
        logging.info(f"User {user_id} connected")

    async def disconnect(self, user_id: str, websocket: WebSocket):
        """Удаление соединения"""

        if (user_id in self.active_connections and
            self.active_connections[user_id] == websocket
        ):
            del self.active_connections[user_id]
        
        await self.redis_service.hdel("active_connections", user_id)
        logging.info(f"User {user_id} disconnected")

    async def send_personal_message(self, user_id: str, message: str):
        """Отправка сообщения конкретному пользователю"""

        websocket: WebSocket = self.active_connections.get(user_id)
        json_message = json.dumps(message, ensure_ascii=False)
        
        if websocket:
            try:
                await websocket.send_text(json_message)
                logging.debug(f"Message sent to user {user_id}")
                return True
            except Exception as e:
                logging.warning(f"Failed to send to user {user_id}: {str(e)}")
                await self.disconnect(user_id, websocket)
                return False

        connection_info = await self.redis_service.hget(
            "active_connections", user_id
        )
        if not connection_info:
            logging.warning(f"No active connection for user {user_id}")
            return False
        
        try:
            connection_info = json.loads(connection_info)
            return True
        except Exception as e:
            logging.error(f"Error sending to user {user_id}: {str(e)}")
            return False

    async def broadcast(self, message: str):
        """Отправка сообщения всем подключенным пользователям"""

        tasks = []
        for user_id, _ in self.active_connections.items():
            tasks.append(self.send_personal_message(user_id, message))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success_count = sum(1 for r in results if r is True)
        logging.info(
            f"Broadcasted to {success_count}/"
            f"{len(self.active_connections)} users"
        )

    async def close_all(self):
        """Закрытие всех активных соединений"""

        for user_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.close(code=1001, reason="Server shutdown")
            except Exception:
                pass
            await self.disconnect(user_id, websocket)
