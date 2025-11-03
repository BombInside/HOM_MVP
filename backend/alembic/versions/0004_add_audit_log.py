"""add audit log table

Revision ID: 0004_add_audit_log
Revises: 0003_equipment_models
Create Date: 2025-11-03 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_add_audit_log"
down_revision = "0003_equipment_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("table_name", sa.String(length=128), nullable=False),
        sa.Column("object_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("old_data", sa.JSON(), nullable=True),
        sa.Column("new_data", sa.JSON(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_log_table", "audit_log", ["table_name"], unique=False)
    op.create_index("ix_audit_log_object", "audit_log", ["object_id"], unique=False)


def downgrade() -> None:
    op.drop_table("audit_log")
