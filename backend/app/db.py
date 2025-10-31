# mypy: ignore-errors
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.config import settings
from app.models import *  # noqa: F401, F403

# --- Асинхронный движок ---
engine = create_async_engine(settings.DB_URL, echo=False, future=True)

# --- Сессия ---
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронный генератор сессий."""
    async with async_session() as session:
        yield session


async def wait_for_db_ready(retries: int = 10, delay: int = 3):
    """Ожидание готовности БД (Postgres может не успеть подняться в Docker)."""
    for attempt in range(retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda conn: None)
            print("✅ Database is ready.")
            return
        except Exception as e:
            print(f"⏳ Waiting for database... ({attempt + 1}/{retries}) - {e}")
            await asyncio.sleep(delay)
    raise RuntimeError("❌ Database connection failed after several attempts.")


async def create_db_and_tables() -> None:
    """Создаёт все таблицы, если их нет."""
    print("🧩 Проверка и создание таблиц...")
    await wait_for_db_ready()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("✅ Все таблицы в БД готовы.")
