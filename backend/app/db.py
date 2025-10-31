from __future__ import annotations

from typing import Any, AsyncGenerator, cast

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

from .config import settings


def get_db_url() -> str:
    return settings.DB_URL


engine: AsyncEngine = create_async_engine(settings.DB_URL, echo=False, future=True)

# ✅ Используем async_sessionmaker вместо sessionmaker
AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for async DB session"""
    async with AsyncSessionLocal() as session:
        yield session


__all__ = ["SQLModel", "engine", "get_session", "get_db_url", "AsyncSession"]
