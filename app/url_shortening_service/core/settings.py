from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_name: str = "URL Shortening Service"
    app_version: str = "1.0.1"
    debug: bool = False
    environment: str = "development"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    base_url: str = "http://localhost:8000"
    
    # Database settings
    database_url: str = "postgresql://postgres:password@localhost:5432/url_shortener"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_cache_ttl: int = 3600
    
    # Security settings
    secret_key: str = "your-secret-key-change-in-production"
    
    # URL shortener settings
    short_code_length: int = 6
    max_generation_attempts: int = 5
    default_expiration_hours: int = 168  # 7 days
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        allowed_schemes = [
            'postgresql://',
            'postgresql+psycopg2://',
            'postgresql+asyncpg://',
        ]
        if not any(v.startswith(scheme) for scheme in allowed_schemes):
            raise ValueError('Database URL must be PostgreSQL with a supported driver')
        return v
    
    @field_validator('redis_url')
    @classmethod
    def validate_redis_url(cls, v):
        if not v.startswith('redis://'):
            raise ValueError('Redis URL must start with redis://')
        return v
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }

# Create global settings instance
settings = Settings()