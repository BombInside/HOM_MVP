from __future__ import annotations
import json
from typing import List, Any, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = Field(default="dev")
    DB_URL: str = Field(default="postgresql+asyncpg://hom_user:hom_pass@postgres:5432/hom_db")
    JWT_SECRET: str = Field(default="bc45811b156fdbc0f5e49e0554b56d311c7e3d207392943347e2cb100b49b1e2")
    JWT_EXPIRE_MIN: int = Field(default=60)
    REDIS_URL: str = Field(default="redis://redis:6379")

    # 👇 здесь ключевое отличие — Union[str, List[str]]
    CORS_ORIGINS: Union[str, List[str]] = Field(default_factory=lambda: ["http://localhost:5173"])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Поддерживает CORS_ORIGINS в форматах:
        - JSON: ["https://a.com", "https://b.com"]
        - CSV:  https://a.com,https://b.com
        - Один URL: https://a.com
        """
        if not v:
            return ["http://localhost:5173"]

        if isinstance(v, list):
            return v

        if isinstance(v, str):
            v = v.strip()
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
