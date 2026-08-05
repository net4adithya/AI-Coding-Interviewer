# python_backend/app/config.py

"""Application configuration loaded from .env using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
import os

class Settings(BaseSettings):
    PORT: int = 3001
    DATABASE_URL: str = "sqlite:///./test.db"
    JWT_SECRET: str = "super_secret_access_token_key_change_me_in_production_12345"
    JWT_EXPIRATION: str = "15m"
    JWT_REFRESH_SECRET: str = "super_secret_refresh_token_key_change_me_in_production_67890"
    JWT_REFRESH_EXPIRATION: str = "7d"

    model_config = ConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
        env_file_encoding="utf-8",
        extra="allow",
    )

settings = Settings()
