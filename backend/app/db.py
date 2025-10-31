from __future__ import annotations

from typing import Any, AsyncGenerator, cast

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from .config import settings


def get_db_url() -> str:
    """Алебик/env.py дергает эту функцию; оставляем здесь для совместимости."""
    return settings.DB_URL


# Движок
engine: AsyncEngine = create_async_engine(settings.DB_URL, echo=False, future=True)

# sessionmaker со строгой типизацией (обход ограничений типовых аннотаций sqlalchemy-stubs)
AsyncSessionLocal = sessionmaker(
    bind=cast(Any, engine),
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость FastAPI для выдачи async-сессии."""
    async with AsyncSessionLocal() as session:
        yield session


__all__ = ["SQLModel", "engine", "get_session", "get_db_url", "AsyncSession"]
