from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "FraudShield AI"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    JWT_SECRET_KEY: str = "supersecret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "fraudshield-api"
    
    RISK_LOW_MAX: int = 30
    RISK_MEDIUM_MAX: int = 70
    
    RATE_LIMIT_PER_MINUTE: int = 60
    
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    ML_MODEL_PATH: str = "./ml/models"
    ML_ACTIVE_MODEL_VERSION: str = "v1"
    
    GEMINI_API_KEY: str = ""
    
    MLFLOW_TRACKING_URI: str = "http://localhost:5001"
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore")

settings = Settings()
