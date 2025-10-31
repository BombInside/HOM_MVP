import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from alembic import context
from app.config import settings
from app.models import *  # noqa: F401, F403 — импортируем все модели, чтобы Alembic видел таблицы

# ----------------------------------------------------
# Alembic configuration setup
# ----------------------------------------------------
config = context.config
config.set_main_option("sqlalchemy.url", settings.DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# SQLModel metadata — Alembic будет отслеживать все таблицы
target_metadata = SQLModel.metadata


# ----------------------------------------------------
# Offline mode (dump SQL)
# ----------------------------------------------------
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    context.configure(
        url=settings.DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ----------------------------------------------------
# Online mode (apply migrations to real DB)
# ----------------------------------------------------
def do_run_migrations(connection):
    """Sync execution inside async context."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    """Run migrations in 'online' mode (async)."""
    connectable = create_async_engine(
        settings.DB_URL,
        poolclass=pool.NullPool,
        future=True,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# ----------------------------------------------------
# Entrypoint
# ----------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
