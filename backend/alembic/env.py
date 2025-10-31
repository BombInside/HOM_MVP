from logging.config import fileConfig
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from app.db import SQLModel, get_db_url

# Alembic Config object, provides access to the .ini file
config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = SQLModel.metadata


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    engine = create_async_engine(get_db_url(), echo=False)
    with engine.sync_engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
