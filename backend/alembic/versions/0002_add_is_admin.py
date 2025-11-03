"""Add column is_admin to user table (safe migration)

Revision ID: 0002_add_is_admin
Revises: 0001_init
Create Date: 2025-11-01 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision: str = "0002_add_is_admin"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Добавляем колонку is_admin, если её нет ---
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("user")]

    if "is_admin" not in columns:
        op.add_column(
            "user",
            sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        )
        op.execute("UPDATE \"user\" SET is_admin = false WHERE is_admin IS NULL;")
        op.alter_column("user", "is_admin", server_default=None)  # убираем дефолт после заполнения


def downgrade() -> None:
    # --- Безопасное удаление поля при откате ---
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns("user")]
    if "is_admin" in columns:
        op.drop_column("user", "is_admin")
