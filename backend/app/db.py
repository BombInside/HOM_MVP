# mypy: ignore-errors
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.config import settings
from app.models import *  # ✅ важно: чтобы SQLModel знал все таблицы


# --- Асинхронный движок SQLAlchemy ---
engine = create_async_engine(settings.DB_URL, future=True, echo=False)

# --- Асинхронная фабрика сессий ---
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий для Depends."""
    async with async_session() as session:
        yield session


async def create_db_and_tables() -> None:
    """
    Создаёт все таблицы в базе данных, если они ещё не существуют.
    Гарантирует, что Permission/Role/User будут созданы до RBAC сидирования.
    """
    print("🧩 Проверка структуры БД...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ Все таблицы проверены или созданы.")


__all__ = [
    "engine",
    "async_session",
    "get_session",
    "create_db_and_tables",
    "SQLModel",
]
