import os
from typing import Optional, List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    class BaseSettings:
        pass

class Settings(BaseSettings):
    PROJECT_NAME: str = "Meu Carro API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./meu_carro.db")

    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "meu_carro_super_secret_jwt_key_change_in_production_2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 30  # Sincronizado com o trial de 30 dias

    # Trial
    TRIAL_DAYS: int = 30

    # Google Gemini AI (Isolada no backend)
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY", None)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    RATE_LIMIT_AI_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_AI_PER_MINUTE", "10"))

    # Storage (S3 compatível)
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")  # local ou s3
    STORAGE_ENDPOINT: Optional[str] = os.getenv("STORAGE_ENDPOINT", None)
    STORAGE_BUCKET: str = os.getenv("STORAGE_BUCKET", "meu-carro-receipts")
    STORAGE_ACCESS_KEY: Optional[str] = os.getenv("STORAGE_ACCESS_KEY", None)
    STORAGE_SECRET_KEY: Optional[str] = os.getenv("STORAGE_SECRET_KEY", None)
    LOCAL_STORAGE_DIR: str = os.getenv("LOCAL_STORAGE_DIR", "./uploads")

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
