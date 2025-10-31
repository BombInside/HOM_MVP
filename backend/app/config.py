from __future__ import annotations

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = Field(default="dev")
    DB_URL: str = Field(default="postgresql+asyncpg://hom_user:hom_pass@postgres:5432/hom_db")
    JWT_SECRET: str = Field(default="dev-secret-change-me")
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    class Config:
        env_file = ".env"
        extra = "ignore"


# Единый инстанс для импорта в проекте
settings = Settings()
