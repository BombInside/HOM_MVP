from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from .config import settings

engine = create_async_engine(settings.DB_URL, future=True, echo=False)

# корректная асинхронная фабрика сессий
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# экспортируем SQLModel для Alembic
__all__ = ["get_session", "SQLModel"]

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
