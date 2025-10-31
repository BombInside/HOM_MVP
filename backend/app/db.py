from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.config import settings


# Создаём асинхронный движок
engine = create_async_engine(settings.DB_URL, future=True, echo=False)

# Асинхронная фабрика сессий
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессии для использования в Depends."""
    async with async_session() as session:
        yield session


async def create_db_and_tables() -> None:
    """
    Создаёт все таблицы в базе данных, если они ещё не существуют.
    Используется при старте приложения перед RBAC сидированием.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


__all__ = [
    "engine",
    "async_session",
    "get_session",
    "create_db_and_tables",
    "SQLModel",
]
