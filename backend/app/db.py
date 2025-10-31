from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel  # noqa: F401  # нужно для Alembic (metadata)

from .config import settings


def get_db_url() -> str:
    return settings.DB_URL


# Создаём AsyncEngine
engine: AsyncEngine = create_async_engine(get_db_url(), echo=False, future=True)

# Фабрика AsyncSession
async_sessionmaker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker() as session:
        yield session
