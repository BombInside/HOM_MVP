# -*- coding: utf-8 -*-
"""
Инициализация подключения к БД (async SQLAlchemy) и фабрика сессий.
Здесь же объявляется декларативная база моделей `Base`, чтобы Alembic и весь проект
могли импортировать ее из единой точки: `from app.db import Base`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import AsyncGenerator, Optional, Callable

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import OperationalError

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ======================================================
# Декларативная база для всех ORM-моделей
# ======================================================
Base = declarative_base()

# ======================================================
# Асинхронный движок и сессия
# ======================================================
# В конфиге используется DATABASE_URL (alias DB_URL) — оставляем как есть.
DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Фабрика асинхронных сессий
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI: выдать асинхронную сессию.
    """
    async with async_session() as session:
        yield session


# ======================================================
# Утилиты для старта приложения
# ======================================================
async def wait_for_db_ready(timeout_sec: int = 30) -> None:
    """
    Ожидание готовности БД. Не делает никаких DDL — только проверка доступности.
    """
    deadline = asyncio.get_event_loop().time() + timeout_sec
    while True:
        try:
            async with engine.begin() as conn:
                # Небольшой no-op, чтобы убедиться в соединении
                await conn.run_sync(lambda _: None)
            logger.info("✅ Database connection is ready.")
            return
        except OperationalError as e:
            if asyncio.get_event_loop().time() > deadline:
                logger.error("❌ Database is not ready in time.", exc_info=e)
                raise
            await asyncio.sleep(1)


async def create_db_and_tables() -> None:
    """
    Создание всех таблиц из метадаты моделей (когда это необходимо).
    В проде обычно делается миграциями Alembic, но для дев-окружения удобно.
    """
    from app.models import Base as ModelsBase  # гарантируем, что все модели импортированы
    assert ModelsBase is Base, "Ожидалось, что app.models.Base и app.db.Base — это один и тот же объект."

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
