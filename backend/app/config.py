from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Общие
    APP_ENV: str = Field(default="dev")

    # База данных
    DB_URL: str = Field(
        default="postgresql+asyncpg://hom_user:hom_pass@postgres:5432/hom_db"
    )

    # Аутентификация
    JWT_SECRET: str = Field(default="dev-secret")
    JWT_EXPIRE_MIN: int = Field(default=60)

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379")

    class Config:
        env_file = ".env"
        extra = "ignore"


# Глобальный инстанс настроек (чтобы mypy видел атрибут `settings`)
settings = Settings()


def get_settings() -> Settings:
    """Фабрика для DI при необходимости."""
    return settings
