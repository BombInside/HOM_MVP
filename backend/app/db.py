# -*- coding: utf-8 -*-
"""
Инициализация подключения к БД (async SQLAlchemy) и фабрика сессий.
Теперь декларативная база моделей (`Base`) импортируется из app.models.base.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.models.base import Base  # <-- единая точка истины

logger = logging.getLogger(__name__)
settings = get_settings()

# ======================================================
# Асинхронный движок и фабрика сессий
# ======================================================
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# ======================================================
# Dependency для FastAPI
# ======================================================
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронная сессия SQLAlchemy для FastAPI."""
    async with async_session() as session:
        yield session


# ======================================================
# Утилиты инициализации
# ======================================================
async def wait_for_db_ready(timeout_sec: int = 30) -> None:
    """Проверка доступности базы данных."""
    deadline = asyncio.get_event_loop().time() + timeout_sec
    while True:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda _: None)
            logger.info("✅ Database connection is ready.")
            return
        except OperationalError as e:
            if asyncio.get_event_loop().time() > deadline:
                logger.error("❌ Database is not ready in time.", exc_info=e)
                raise
            await asyncio.sleep(1)


async def create_db_and_tables() -> None:
    """Создание таблиц из всех импортированных моделей."""
    from app.models import Base as ModelsBase
    assert (
        ModelsBase is Base
    ), "Ожидалось, что app.models.Base и app.db.Base — это один и тот же объект."
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
