# -*- coding: utf-8 -*-
"""
Alembic env для асинхронных миграций.
Гарантированно находит приложение в Docker, импортирует Settings и Base,
и прогоняет миграции поверх async-engine.
"""

from __future__ import annotations

import os
import sys
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

# ----------------------------------------------------
# Пути, чтобы Alembic видел наше приложение
# (backend/alembic/env.py -> добавляем backend/ и backend/app в sys.path)
# ----------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../backend
APP_DIR = os.path.join(BASE_DIR, "app")

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)

# Конфигурация и логирование Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----------------------------------------------------
# Импорты приложения (после настройки путей!)
# ----------------------------------------------------
from app.config import get_settings
from app.models import Base  # <-- из app.models, где Base = app.db.Base

settings = get_settings()

# Устанавливаем URL БД для Alembic из настроек
DATABASE_URL = settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# ----------------------------------------------------
# Метадата моделей (чтобы работал autogenerate)
# ----------------------------------------------------
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (генерация SQL без подключения)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # учитываем изменение типов (в т.ч. Enum)
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Общий ран миграций для online-режима."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Онлайн-режим миграций с async-движком."""
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
