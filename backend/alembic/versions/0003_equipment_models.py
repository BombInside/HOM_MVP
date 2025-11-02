"""add equipment models: lines, machines, repairs, repair_attachments

Revision ID: 0003_equipment_models
Revises: 0002_add_is_admin
Create Date: 2025-11-02 12:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum


# revision identifiers, used by Alembic.
revision = "0003_equipment_models"
down_revision = "0002_add_is_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------
    # 1) Идемпотентно создаём ENUM-типы напрямую в PostgreSQL
    #    (на случай повторного запуска — не упадёт на duplicate_object)
    # ------------------------------------------------------------
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE line_status AS ENUM ('working','maintenance','stopped');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE machine_status AS ENUM ('operational','broken','maintenance','active');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE repair_type AS ENUM ('scheduled','unscheduled');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)
    op.execute("""
    DO $$ BEGIN
        CREATE TYPE repair_status AS ENUM ('open','in_progress','closed');
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)

    # ------------------------------------------------------------
    # 2) Регистрируем их в SQLAlchemy как уже существующие типы
    #    ВАЖНО: используем PGEnum только по имени типа (без значений!)
    #    и create_type=False — это отключает любое CREATE TYPE.
    # ------------------------------------------------------------
    bind = op.get_bind()
    for name in ("line_status", "machine_status", "repair_type", "repair_status"):
        PGEnum(name=name, create_type=False).create(bind, checkfirst=True)

    line_status = PGEnum(name="line_status", create_type=False)
    machine_status = PGEnum(name="machine_status", create_type=False)
    repair_type = PGEnum(name="repair_type", create_type=False)
    repair_status = PGEnum(name="repair_status", create_type=False)

    # ------------------------------------------------------------
    # 3) Таблицы
    # ------------------------------------------------------------
    op.create_table(
        "lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", line_status, nullable=False, server_default="working"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        # ВАЖНО: в 0001_init таблица называется "user" (в ед. числе)
        sa.Column("deleted_by", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL")),
    )

    op.create_table(
        "machines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("line_id", sa.Integer(), sa.ForeignKey("lines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("status", machine_status, nullable=False, server_default="operational"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_by", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL")),
    )

    op.create_table(
        "repairs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("machine_id", sa.Integer(), sa.ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("repair_type", repair_type, nullable=False, server_default="unscheduled"),
        sa.Column("status", repair_status, nullable=False, server_default="open"),
        # Совместимо с 0001_init (таблица user)
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "repair_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repair_id", sa.Integer(), sa.ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_name", sa.String(256), nullable=False),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL")),
    )


def downgrade() -> None:
    op.drop_table("repair_attachments")
    op.drop_table("repairs")
    op.drop_table("machines")
    op.drop_table("lines")

    # Чистим типы (идемпотентно)
    for tname in ("line_status", "machine_status", "repair_type", "repair_status"):
        op.execute(f"DROP TYPE IF EXISTS {tname} CASCADE;")
