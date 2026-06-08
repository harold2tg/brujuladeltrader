"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str
    DEBUG: bool = True

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Encryption
    ENCRYPTION_KEY: str

    # Storage
    STORAGE_TYPE: str = "local"
    STORAGE_LOCAL_PATH: str = "/app/uploads"

    # Plan limits
    FREE_PLAN_MAX_UPLOADS: int = 5
    FREE_PLAN_MAX_AI_CALLS_PER_DAY: int = 10
    FREE_PLAN_MAX_ALERT_RULES: int = 3
    MAX_UPLOAD_SIZE_MB: int = 10

    # cTrader
    CTRADER_HOST_LIVE: str = "live.ctraderapi.com"
    CTRADER_HOST_DEMO: str = "demo.ctraderapi.com"
    CTRADER_PORT: int = 5035

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"


settings = Settings()
