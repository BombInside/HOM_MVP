# -*- coding: utf-8 -*-
"""
Инициализация подключения к БД (async SQLAlchemy/SQLModel) и фабрика сессий.
"""

from __future__ import annotations
from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import OperationalError
import asyncio
from .config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость FastAPI для выдачи асинхронной сессии БД."""
    async with SessionLocal() as session:
        yield session


async def create_db_and_tables() -> None:
    """
    Создаёт таблицы только в DEV/TEST окружениях.
    В проде для миграций использовать Alembic (alembic upgrade head).
    """
    if settings.ENV.lower() in {"dev", "development", "test"}:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)


async def wait_for_db_ready(timeout_sec: int = 30) -> None:
    """
    Ожидание готовности БД (хелпер для старта сервиса).
    """
    deadline = asyncio.get_event_loop().time() + timeout_sec
    while True:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda _: None)
            return
        except OperationalError:
            if asyncio.get_event_loop().time() > deadline:
                raise
            await asyncio.sleep(1)
