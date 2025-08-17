from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings"""
    service_name: str = "payment-service"
    service_port: int = 8000
    
    # Payment provider
    payment_provider: str = "yookassa"  # Can be switched to other providers
    
    # YooKassa settings
    yookassa_shop_id: str
    yookassa_secret_key: str
    
    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # External services
    auth_service_url: str = "http://auth-service:8001"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()