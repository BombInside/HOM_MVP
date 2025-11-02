"""add equipment models: lines, machines, repairs, repair_attachments

Revision ID: 0003_equipment_models
Revises: 0002_add_is_admin
Create Date: 2025-11-02 12:00:00.000000
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_equipment_models"
down_revision = "0002_add_is_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- enums ---
    line_status = sa.Enum("working", "maintenance", "stopped", name="line_status")
    machine_status = sa.Enum("operational", "broken", "maintenance", name="machine_status")
    repair_type = sa.Enum("scheduled", "unscheduled", name="repair_type")
    repair_status = sa.Enum("open", "in_progress", "closed", name="repair_status")

    line_status.create(op.get_bind(), checkfirst=True)
    machine_status.create(op.get_bind(), checkfirst=True)
    repair_type.create(op.get_bind(), checkfirst=True)
    repair_status.create(op.get_bind(), checkfirst=True)

    # --- lines ---
    op.create_table(
        "lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=64), nullable=False, unique=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", line_status, nullable=False, server_default="working"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_lines_code", "lines", ["code"], unique=True)
    op.create_index("ix_lines_is_active", "lines", ["is_active"], unique=False)
    op.create_index("ix_lines_status", "lines", ["status"], unique=False)

    # --- machines ---
    op.create_table(
        "machines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("line_id", sa.Integer(), sa.ForeignKey("lines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("asset_number", sa.String(length=128), nullable=True),
        sa.Column("serial_number", sa.String(length=128), nullable=True),
        sa.Column("manufacturer", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("type", sa.String(length=128), nullable=True),
        sa.Column("status", machine_status, nullable=False, server_default="operational"),
        sa.Column("last_repair_date", sa.Date(), nullable=True),
        sa.Column("hours_since_last_repair", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_machines_line_id", "machines", ["line_id"], unique=False)
    op.create_index("ix_machines_status", "machines", ["status"], unique=False)
    op.create_index("ix_machines_active", "machines", ["is_active"], unique=False)
    op.create_index("ix_machines_asset_number", "machines", ["asset_number"], unique=False)
    op.create_index("ix_machines_serial_number", "machines", ["serial_number"], unique=False)

    # --- repairs ---
    op.create_table(
        "repairs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("machine_id", sa.Integer(), sa.ForeignKey("machines.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("asset_number", sa.String(length=128), nullable=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("actions_taken", sa.Text(), nullable=True),
        sa.Column("performed_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("repair_type", repair_type, nullable=False, server_default="unscheduled"),
        sa.Column("status", repair_status, nullable=False, server_default="open"),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("parts_used", sa.Text(), nullable=True),
        sa.Column("downtime_hours", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_repairs_machine_id", "repairs", ["machine_id"], unique=False)
    op.create_index("ix_repairs_status", "repairs", ["status"], unique=False)
    op.create_index("ix_repairs_type", "repairs", ["repair_type"], unique=False)
    op.create_index("ix_repairs_asset_number", "repairs", ["asset_number"], unique=False)
    op.create_index("ix_repairs_created_at", "repairs", ["created_at"], unique=False)

    # --- repair_attachments ---
    op.create_table(
        "repair_attachments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repair_id", sa.Integer(), sa.ForeignKey("repairs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_name", sa.String(length=256), nullable=False),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_repair_attachments_repair_id", "repair_attachments", ["repair_id"], unique=False)


def downgrade() -> None:
    op.drop_table("repair_attachments")
    op.drop_index("ix_repairs_created_at", table_name="repairs")
    op.drop_index("ix_repairs_asset_number", table_name="repairs")
    op.drop_index("ix_repairs_type", table_name="repairs")
    op.drop_index("ix_repairs_status", table_name="repairs")
    op.drop_index("ix_repairs_machine_id", table_name="repairs")
    op.drop_table("repairs")

    op.drop_index("ix_machines_serial_number", table_name="machines")
    op.drop_index("ix_machines_asset_number", table_name="machines")
    op.drop_index("ix_machines_active", table_name="machines")
    op.drop_index("ix_machines_status", table_name="machines")
    op.drop_index("ix_machines_line_id", table_name="machines")
    op.drop_table("machines")

    op.drop_index("ix_lines_status", table_name="lines")
    op.drop_index("ix_lines_is_active", table_name="lines")
    op.drop_index("ix_lines_code", table_name="lines")
    op.drop_table("lines")

    # enums
    op.execute("DROP TYPE IF EXISTS line_status")
    op.execute("DROP TYPE IF EXISTS machine_status")
    op.execute("DROP TYPE IF EXISTS repair_type")
    op.execute("DROP TYPE IF EXISTS repair_status")
