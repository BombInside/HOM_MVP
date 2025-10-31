from __future__ import annotations

import json
from typing import List, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = Field(default="dev")
    DB_URL: str = Field(default="postgresql+asyncpg://hom_user:hom_pass@postgres:5432/hom_db")
    JWT_SECRET: str = Field(default="dev-secret-change-me")
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- Гибкий парсер для CORS_ORIGINS ---
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """
        Поддерживает разные варианты формата переменной CORS_ORIGINS:
        - JSON: ["https://a.com", "https://b.com"]
        - CSV:  https://a.com,https://b.com
        - Один URL: https://a.com
        """
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # Попробуем распарсить как JSON
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Если CSV — разбиваем по запятым
            return [x.strip() for x in v.split(",") if x.strip()]
        return ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        extra = "ignore"


# --- Глобальный инстанс ---
settings = Settings()
