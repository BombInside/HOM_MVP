"""Make audit_log.object_id nullable and seed admin role/permissions (aligned with permission.code)"""

from alembic import op
import sqlalchemy as sa

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

    # 2️⃣ Добавить базовые роли и права, согласованные с 0001_init/0005
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Если нет permission / role / role_permission_link — просто выходим
    if not inspector.has_table("permission") or not inspector.has_table(
        "role"
    ) or not inspector.has_table("role_permission_link"):
        print(
            "⚠️ permission/role/role_permission_link table missing, skipping seeding."
        )
        return

    perm_columns = [c["name"] for c in inspector.get_columns("permission")]
    if "code" not in perm_columns:
        print(
            "⚠️ permission table does not have 'code' column; skipping seeding to avoid schema conflicts."
        )
        return

    # создаём дополнительные permission'ы (через code)
    permissions = [
        {"code": "view", "description": "View records"},
        {"code": "edit", "description": "Edit records"},
        {"code": "delete", "description": "Delete records"},
        {"code": "admin", "description": "Full administrative access"},
    ]
    for perm in permissions:
        conn.execute(
            sa.text(
                """
                INSERT INTO permission (code, description)
                VALUES (:code, :description)
                ON CONFLICT (code) DO NOTHING
                """
            ),
            perm,
        )

    # создаём/находим роль admin (учитываем разные варианты имени)
    admin_id = conn.execute(
        sa.text("SELECT id FROM role WHERE lower(name) = 'admin'")
    ).scalar()
    if not admin_id:
        conn.execute(
            sa.text(
                """
                INSERT INTO role (name, description)
                VALUES ('admin', 'Full access')
                ON CONFLICT (name) DO NOTHING
                """
            )
        )
        admin_id = conn.execute(
            sa.text("SELECT id FROM role WHERE lower(name) = 'admin'")
        ).scalar()

    if not admin_id:
        print("⚠️ Could not ensure admin role; skipping permission linking.")
        return

    # привязка всех прав к admin
    conn.execute(
        sa.text(
            """
            INSERT INTO role_permission_link (role_id, permission_id)
            SELECT :admin_id, p.id
            FROM permission p
            ON CONFLICT DO NOTHING
            """
        ),
        {"admin_id": admin_id},
    )

    print(
        "✅ audit_log.object_id is now nullable; admin role and base permissions ensured/linked"
    )


def downgrade() -> None:
    # Возвращаем object_id к NOT NULL
    op.alter_column(
        "audit_log",
        "object_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    conn = op.get_bind()

    # Чистка связей и базовых добавленных кодов (осторожно, без трогания 0001_init)
    conn.execute(
        sa.text(
            "DELETE FROM role_permission_link WHERE role_id IN (SELECT id FROM role WHERE lower(name) = 'admin');"
        )
    )
    for code in ["view", "edit", "delete", "admin"]:
        conn.execute(
            sa.text("DELETE FROM permission WHERE code = :code"),
            {"code": code},
        )

    # Роль 'Admin' (с заглавной) чистим отдельно, чтобы не трогать 'admin'
    conn.execute(sa.text("DELETE FROM role WHERE name='Admin';"))

    print(
        "🔁 audit_log.object_id reverted and additional admin-related permissions cleaned up"
    )
