from logging.config import fileConfig
from alembic import context
from sqlmodel import SQLModel
from app.db import engine
from app import models  # noqa

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

def run_migrations_offline():
    url = str(engine.url)
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine.sync_engine
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
