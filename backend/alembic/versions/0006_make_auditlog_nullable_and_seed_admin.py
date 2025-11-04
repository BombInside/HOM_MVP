"""Make audit_log.object_id nullable and seed admin role/permissions"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers
revision = "0006_make_auditlog_nullable_and_seed_admin"
down_revision = "0005_seed_admin_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1️⃣ Сделать object_id nullable
    op.alter_column(
        "audit_log",
        "object_id",
        existing_type=sa.Integer(),
        nullable=True,
    )

    # 2️⃣ Добавить базовые роли и права
    conn = op.get_bind()

    # создаём permission'ы
    permissions = [
        {"name": "view", "description": "View records"},
        {"name": "edit", "description": "Edit records"},
        {"name": "delete", "description": "Delete records"},
        {"name": "admin", "description": "Full administrative access"},
    ]
    for perm in permissions:
        conn.execute(
            sa.text(
                """
                INSERT INTO permission (name, description)
                VALUES (:name, :description)
                ON CONFLICT (name) DO NOTHING
                """
            ),
            perm,
        )

    # создаём роль Admin
    conn.execute(
        sa.text(
            """
            INSERT INTO role (name, description)
            VALUES ('Admin', 'Full access')
            ON CONFLICT (name) DO NOTHING
            """
        )
    )

    # привязка прав к Admin
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permission_link (role_id, permission_id)
            SELECT r.id, p.id FROM role r, permission p
            WHERE r.name = 'Admin'
            ON CONFLICT DO NOTHING
            """
        )
    )

    print("✅ audit_log.object_id is now nullable; Admin role and base permissions seeded")


def downgrade() -> None:
    op.alter_column(
        "audit_log",
        "object_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.execute("DELETE FROM role_permission_link WHERE role_id IN (SELECT id FROM role WHERE name='Admin');")
    op.execute("DELETE FROM role WHERE name='Admin';")
    for name in ["view", "edit", "delete", "admin"]:
        op.execute(f"DELETE FROM permission WHERE name='{name}';")
    print("🔁 audit_log.object_id reverted and Admin role removed")
