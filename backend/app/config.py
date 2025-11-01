# -*- coding: utf-8 -*-
"""
Модуль конфигурации приложения.
Все секреты и параметры берутся из переменных окружения.
Дефолтные значения максимально безопасны для разработки и НЕ должны применяться в продакшене.
"""

from __future__ import annotations
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
import json


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

    # CORS (строгий список, по умолчанию пустой)
    CORS_ORIGINS: List[AnyHttpUrl] = []

    # Логи
    LOG_JSON: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _coerce_cors(cls, v):
        """
        Универсальный парсер CORS_ORIGINS:
        - принимает JSON-массив (строка вида '["url1","url2"]')
        - принимает строку через запятую ('url1,url2')
        - принимает список
        """
        if not v:
            return []
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    raise ValueError("Неверный формат CORS_ORIGINS (JSON parse error)")
            return [x.strip() for x in v.split(",") if x.strip()]
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Кэшированный доступ к настройкам, чтобы не пересоздавать объект Settings."""
    return Settings()  # type: ignore[misc]
