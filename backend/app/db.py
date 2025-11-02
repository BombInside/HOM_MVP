# -*- coding: utf-8 -*-
"""
Инициализация подключения к БД (async SQLAlchemy) и фабрика сессий.
Авто-создание таблиц отключено: применяем только Alembic миграции.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import OperationalError

from app.config import get_settings
from app.models.base import Base  # базовый declarative Base (тут не используем create_all)

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
    pool_pre_ping=True,
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
# Health-check БД
# ======================================================
async def wait_for_db_ready(timeout_sec: int = 30) -> None:
    """
    Аккуратно ждём готовности БД.
    Ничего не создаём — просто проверяем подключение транзакцией BEGIN/COMMIT.
    """
    deadline = asyncio.get_event_loop().time() + timeout_sec
    attempt = 0
    while True:
        attempt += 1
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda _: None)
            logger.info("✅ Database connection is ready.")
            return
        except OperationalError as e:
            if asyncio.get_event_loop().time() > deadline:
                logger.error("❌ Database is not ready in time (attempt %d).", attempt, exc_info=e)
                raise
            await asyncio.sleep(1)

# ======================================================
# (Опционально) программный запуск Alembic в DEV
# ======================================================
async def run_alembic_upgrade(revision: str = "head") -> Optional[int]:
    """
    НЕ вызывается автоматически.
    Можно вручную вызвать из dev-скрипта старта,
    чтобы применить миграции: await run_alembic_upgrade("head")
    """
    # Не тянем Alembic как runtime-зависимость продакшена, вызываем только при наличии
    if os.environ.get("ENABLE_PROGRAMMATIC_ALEMBIC", "0") != "1":
        logger.info("Alembic programmatic upgrade is disabled. Set ENABLE_PROGRAMMATIC_ALEMBIC=1 to enable.")
        return None

    try:
        # Ленивая импортируемость, чтобы не поднимать требования в рантайме
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        # Важно: alembic.ini должен быть корректно сконфигурирован на тот же DATABASE_URL

        logger.info("▶️  Running alembic upgrade %s ...", revision)
        command.upgrade(alembic_cfg, revision)
        logger.info("✅ Alembic upgrade %s done.", revision)
        return 0
    except Exception:
        logger.exception("❌ Alembic upgrade failed.")
        return 1
