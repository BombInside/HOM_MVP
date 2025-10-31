from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.db import SQLModel, settings

config = context.config
fileConfig(config.config_file_name)
target_metadata = SQLModel.metadata

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    connectable = create_async_engine(settings.DB_URL, future=True)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

import asyncio
asyncio.run(run_migrations_online())
