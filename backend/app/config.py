# -*- coding: utf-8 -*-
"""
Модуль конфигурации приложения.
Все секреты и параметры берутся из переменных окружения.
Дефолтные значения максимально безопасны для разработки и НЕ должны применяться в продакшене.
"""

from __future__ import annotations
from functools import lru_cache
from typing import List, Union
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
    CORS_ORIGINS: Union[List[AnyHttpUrl], str] = []

    # Логи
    LOG_JSON: bool = True
    LOG_LEVEL: str = "INFO"

    class Config:
        case_sensitive = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """
        Универсальный парсер CORS_ORIGINS:
        поддерживает строку, CSV, JSON-массив и список.
        """
        if not v:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            # JSON-массив, например: '["http://a","http://b"]'
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    raise ValueError("Неверный формат JSON в CORS_ORIGINS")
            # одиночный URL без запятых
            if v.startswith("http") and "," not in v:
                return [v]
            # список через запятую
            return [x.strip() for x in v.split(",") if x.strip()]
        raise TypeError("Неверный тип для CORS_ORIGINS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Кэшированный доступ к настройкам, чтобы не пересоздавать объект Settings."""
    return Settings()  # type: ignore[misc]
