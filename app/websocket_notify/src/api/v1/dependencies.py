from fastapi import WebSocket

from src.services.connection_manager import ConnectionManager


def get_connection_manager(websocket: WebSocket) -> ConnectionManager:
    """Получаем connection manager."""
    return websocket.app.container.connection_manager()