from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "dev"
    db_url: str = "postgresql+asyncpg://root@cockroachdb:26257/hom?sslmode=disable"
    jwt_secret: str = "change-me"
    jwt_expire_min: int = 60
    cors_origins: str = "http://localhost:5173"
    class Config:
        env_prefix = ""
        case_sensitive = False

settings = Settings()
