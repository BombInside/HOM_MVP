# -*- coding: utf-8 -*-
"""
PostgreSQL-safe helpers for Alembic and SQLAlchemy.
Используется для идемпотентного (безошибочного) создания ENUM-типов.
"""

from __future__ import annotations
from sqlalchemy import text
from alembic import op


def create_enum_safe(name: str, values: list[str]) -> None:
    """
    Безопасно создаёт ENUM в PostgreSQL.
    Если тип уже существует — игнорирует.
    """
    escaped_values = ",".join(f"'{v}'" for v in values)
    ddl = f"""
    DO $$ BEGIN
        CREATE TYPE {name} AS ENUM ({escaped_values});
    EXCEPTION WHEN duplicate_object THEN
        NULL;
    END $$;
    """
    op.execute(text(ddl))


def drop_enum_safe(name: str) -> None:
    """
    Безопасно удаляет ENUM (если существует), с CASCADE.
    """
    op.execute(text(f"DROP TYPE IF EXISTS {name} CASCADE;"))
