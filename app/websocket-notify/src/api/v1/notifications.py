import logging

import httpx
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from src.api.v1.dependencies import get_connection_manager
from src.core.config import get_settings
from src.core.exceptions import InvalidTokenException
from src.core.logger import setup_logging
from src.services.connection_manager import ConnectionManager

setup_logging()

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication"),
    manager: ConnectionManager = Depends(get_connection_manager)
):
    """
    WebSocket endpoint для мгновенных сообщения.
    
    Клиент должен предоставить валидный JWT токен в строке запроса
    """

    try:
        logging.info(f"Getting token: {token}")
        user_id = await validate_token(token)
        logging.info(f"User {user_id} connecting via WebSocket...")
        
        await manager.connect(user_id, websocket)
        logging.info(f"User {user_id} connected")
        
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect as e:
        logging.info(
            f"User {user_id} disconnected "
            f"(code: {e.code}, reason: {e.reason})"
        )
        await manager.disconnect(user_id, websocket)
    except InvalidTokenException:
        logging.warning("Invalid token provided")
        await websocket.close(code=1008, reason="Invalid token")
    except Exception as e:
        logging.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=1011, reason="Internal server error")

async def validate_token(token: str) -> str:
    """
    Проверяем JWT токен в сервисе аутентификации
    
    В случае успеха возвращаем ID пользователя
    """
    
    settings = get_settings()
    try:
        logging.info(
            f"Trying connecting to: {settings.auth_service_url}"
            f"{settings.validate_token_path}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.auth_service_url}{settings.validate_token_path}",
                json={"token": token},
                timeout=2.0
            )
            
            if response.status_code != 200:
                logging.warning(
                    f"Token validation failed: {response.status_code}")
                raise InvalidTokenException()
                
            response_data = response.json()
            if ("user_data" not in response_data 
                or "id" not in response_data["user_data"]
            ):
                logging.warning("Invalid response from auth service")
                raise InvalidTokenException()
                
            user_data = response_data["user_data"]
            return str(user_data["id"])
            
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logging.error(f"Auth service error: {str(e)}")
        raise InvalidTokenException() from e