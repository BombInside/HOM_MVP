from pydantic_settings import BaseSettings
from pydantic import Field, ValidationError

# EN: Settings class definition
# RU: Определение класса настроек
class Settings(BaseSettings):
    app_env: str = "dev"
    db_url: str = "postgresql+asyncpg://root@cockroachdb:26257/hom?sslmode=disable"

    #EN: Add Redis URL for caching and tocken revocation
    #RU: URL Redis для кеширования и отзыва токенов
    redis_url: str = "redis://localhost:6379"
    
    # EN: JWT secret field. We check for a minimum length of 32 characters.
    # RU: Поле JWT секрета. Проверяем минимальную длину в 32 символа.
    jwt_secret: str = Field(
        default="change-me", 
        min_length=32
    )
    
    jwt_expire_min: int = 60
    cors_origins: str = "http://localhost:5173"
    
    class Config:
        env_prefix = ""
        case_sensitive = False

settings = Settings()

# EN: CRITICAL: Raise an error if running outside 'dev' with the default weak secret.
# RU: КРИТИЧЕСКИ: Вызываем ошибку, если запуск происходит вне 'dev' со слабым секретом по умолчанию.
if settings.app_env != "dev" and settings.jwt_secret == "change-me":
    # EN: Fatal error: JWT_SECRET must be set and unique in production environment.
    # RU: Фатальная ошибка: JWT_SECRET должен быть установлен и уникален в production окружении.
    raise ValidationError("FATAL: JWT_SECRET must be set and unique in production environment.")