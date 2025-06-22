from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # MongoDB settings
    mongodb_url: str = Field(default="mongodb://localhost:27017", env="MONGODB_URL")
    mongodb_database: str = Field(default="ugc_service", env="MONGODB_DATABASE")
    
    # API settings
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    project_name: str = Field(default="UGC Service", env="PROJECT_NAME")
    version: str = Field(default="1.0.0", env="VERSION")
    
    # Server settings
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8001, env="PORT")
    
    # Auth settings
    auth_service_url: str = Field(default="http://auth-service:8100", env="AUTH_SERVICE_URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 