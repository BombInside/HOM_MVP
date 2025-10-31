from __future__ import annotations
import json
from typing import List, Any, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = Field(default="dev")
    DB_URL: str = Field(default="postgresql+asyncpg://hom_user:hom_pass@postgres:5432/hom_db")
    JWT_SECRET: str = Field(default="dev-secret-change-me")
    JWT_EXPIRE_MIN: int = Field(default=60)
    REDIS_URL: str = Field(default="redis://redis:6379")
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Парсит CORS_ORIGINS из JSON, CSV или одиночной строки"""
        if v is None:
            return ["http://localhost:5173"]
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["http://localhost:5173"]
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            return [x.strip() for x in v.split(",") if x.strip()]
        return ["http://localhost:5173"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
