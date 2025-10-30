import os
from typing import AsyncGenerator

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# =====================================================
# ✅ DATABASE CONFIGURATION
# =====================================================
DATABASE_URL = os.getenv(
    "DB_URL",
    "postgresql+asyncpg://hom_user:hom_pass@postgres:5432/hom_db"
)


def get_db_url() -> str:
    """Возвращает URL для подключения к базе данных (используется Alembic)."""
    return DATABASE_URL


# =====================================================
# ✅ SQLAlchemy engine & session
# =====================================================
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# =====================================================
# ✅ Dependency для FastAPI
# =====================================================
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для получения асинхронной сессии SQLAlchemy"""
    async with async_session_maker() as session:
        yield session


# =====================================================
# ✅ DB Initialization
# =====================================================
async def init_db() -> None:
    """Создаёт все таблицы, если их нет (для dev-режима)"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


# =====================================================
# ✅ BACKWARD COMPATIBILITY (для GraphQL)
# =====================================================
async_session = async_session_maker  # 👈 добавь эту строку
