# -*- coding: utf-8 -*-
"""
Модуль конфигурации приложения.
Все секреты и параметры берутся из переменных окружения.
Дефолтные значения максимально безопасны для разработки и НЕ должны применяться в продакшене.
"""

from __future__ import annotations
from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator


class Settings(BaseSettings):
    # Базовые
    APP_NAME: str = "HOM Backend"
    DEBUG: bool = False
    ENV: str = "stage"

    # БД
    DATABASE_URL: str

    # JWT / Session
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MIN: int = 60  # срок жизни access-токена в минутах

    # Админ-бустрап (одноразовая форма создания первого администратора)
    ADMIN_BOOTSTRAP_PATH: str = "/adminpanel/bootstrap"

    # CORS (строгий список, по умолчанию пустой; фронтенд должен явно указать домены в .env)
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Логи
    LOG_JSON: bool = True
    LOG_LEVEL: str = "INFO"

    # Безопасность cookies/CSRF в админ-панели можно докрутить позже
    class Config:
        case_sensitive = True

    @field_validator("CORS_ORIGINS", mode="before")
    def _coerce_cors(cls, v):
        # Позволяем строку через запятую -> список
        if not v:
            return []
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Кэшированный доступ к настройкам, чтобы не пересоздавать объект Settings."""
    return Settings()  # type: ignore[misc]
