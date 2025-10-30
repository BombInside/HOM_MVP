python
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    app_env: str = "dev"
    db_url: str = "postgresql+asyncpg://hom_user:hom_pass@postgres:5432/hom_db"
    redis_url: str = "redis://redis:6379"

    jwt_secret: str = Field("change-me", min_length=6)
    jwt_expire_min: int = 60

    cors_origins: str = "http://localhost:5173"

    class Config:
        env_prefix = ""
        case_sensitive = False


settings = Settings()

# Hard fail in non-dev if secret is default
if settings.app_env != "dev" and settings.jwt_secret == "change-me":
    raise RuntimeError("FATAL: JWT_SECRET must be set and unique in non-dev environments.")
