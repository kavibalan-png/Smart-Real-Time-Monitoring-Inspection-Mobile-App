"""
Application configuration — loaded from environment variables.
Never hardcode secrets here.
"""
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Adaptive Inspection Intelligence Platform"
    APP_VERSION: str = "1.0.0-prototype"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./aiip.db"

    # JWT
    SECRET_KEY: str = "dev-secret-key-change-in-production-min32"
    REFRESH_SECRET_KEY: str = "dev-refresh-key-change-in-production-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]
    ALLOWED_VIDEO_TYPES: List[str] = ["video/mp4", "video/webm"]

    # Demo mode flag
    DEMO_MODE: bool = True

    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="allow")


settings = Settings()
