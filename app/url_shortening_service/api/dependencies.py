from core.container import Container
from services.url_service import URLService


container = Container()

def get_url_service() -> URLService:
    """Get URL service instance"""
    return container.url_service()
