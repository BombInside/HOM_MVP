from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_ENV: str = Field("dev")
    DB_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MIN: int = 60
    CORS_ORIGINS: str
    REDIS_URL: str = "redis://redis:6379"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
