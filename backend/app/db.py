import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.config import settings
from app.models import *  # noqa: F401, F403

# --- Асинхронный движок ---
async_engine = create_async_engine(settings.DB_URL, echo=False, future=True)

# --- Асинхронная фабрика сессий ---
async_session = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор для зависимостей FastAPI."""
    async with async_session() as session:
        yield session


async def wait_for_db_ready(retries: int = 15, delay: int = 3):
    """Ждёт, пока база данных будет готова к подключению (актуально в Docker)."""
    for attempt in range(retries):
        try:
            async with async_engine.begin() as conn:
                await conn.run_sync(lambda conn: None)
            print("✅ Database is ready.")
            return
        except Exception as e:
            print(f"⏳ Waiting for database... ({attempt + 1}/{retries}) - {e}")
            await asyncio.sleep(delay)
    raise RuntimeError("❌ Database connection failed after several attempts.")


async def create_db_and_tables() -> None:
    """Создаёт все таблицы, если Alembic ещё не применён."""
    print("🧩 Проверка структуры БД...")
    await wait_for_db_ready()
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ Все таблицы проверены или созданы.")
