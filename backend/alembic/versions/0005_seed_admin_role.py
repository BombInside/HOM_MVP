"""Add admin role and full permissions (aligned with permission.code)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer


# revision identifiers, used by Alembic.
revision = "0005_seed_admin_role"
down_revision = "0004_add_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Lightweight table definitions (на схему БД они не влияют)
    role_table = table(
        "role",
        column("id", Integer),
        column("name", String),
        column("description", String),
    )

    permission_table = table(
        "permission",
        column("id", Integer),
        column("code", String),
        column("description", String),
    )

    link_table = table(
        "role_permission_link",
        column("role_id", Integer),
        column("permission_id", Integer),
    )

    # 1️⃣  Ensure Admin role exists (учитываем и 'admin', и 'Admin')
    admin_id = connection.execute(
        sa.text("SELECT id FROM role WHERE lower(name) = 'admin'")
    ).scalar()

    if not admin_id:
        # Создаём единую роль 'admin' (lowercase) как каноническую
        connection.execute(
            sa.text(
                "INSERT INTO role (name, description) VALUES (:name, :desc)"
            ),
            {"name": "admin", "desc": "Full access to all features"},
        )
        admin_id = connection.execute(
            sa.text("SELECT id FROM role WHERE lower(name) = 'admin'")
        ).scalar()
        print("✅ Created admin role")
    else:
        print("ℹ️ Admin role already exists (admin/Admin)")

    # Если таблицы permission или role_permission_link отсутствуют — выходим
    if not inspector.has_table("permission") or not inspector.has_table(
        "role_permission_link"
    ):
        print(
            "⚠️ permission or role_permission_link table not found, skipping permission creation/linking."
        )
        return

    # Проверяем, что в permission есть колонка code (как в 0001_init)
    perm_columns = [c["name"] for c in inspector.get_columns("permission")]
    if "code" not in perm_columns:
        print(
            "⚠️ permission table does not have 'code' column; skipping permission creation to avoid schema conflicts."
        )
        return

    # 2️⃣  Ensure permissions exist (используем поле code)
    existing_perms = [
        r[0]
        for r in connection.execute(
            sa.text("SELECT code FROM permission")
        ).fetchall()
    ]

    default_perms = [
        ("view", "View access"),
        ("create", "Create access"),
        ("edit", "Edit access"),
        ("delete", "Delete access"),
        ("manage_users", "Manage users"),
        ("manage_roles", "Manage roles"),
        ("manage_settings", "Manage application settings"),
    ]

    for code, desc in default_perms:
        if code not in existing_perms:
            connection.execute(
                sa.text(
                    """
                    INSERT INTO permission (code, description)
                    VALUES (:code, :desc)
                    ON CONFLICT (code) DO NOTHING
                    """
                ),
                {"code": code, "desc": desc},
            )
            print(f"✅ Ensured permission: {code}")

    # 3️⃣  Link admin role to all permissions
    if admin_id:
        perm_ids = [
            r[0]
            for r in connection.execute(
                sa.text("SELECT id FROM permission")
            ).fetchall()
        ]
        for pid in perm_ids:
            exists = connection.execute(
                sa.text(
                    """
                    SELECT 1
                    FROM role_permission_link
                    WHERE role_id = :r AND permission_id = :p
                    """
                ),
                {"r": admin_id, "p": pid},
            ).fetchone()
            if not exists:
                connection.execute(
                    sa.text(
                        """
                        INSERT INTO role_permission_link (role_id, permission_id)
                        VALUES (:r, :p)
                        ON CONFLICT DO NOTHING
                        """
                    ),
                    {"r": admin_id, "p": pid},
                )
        print("✅ Linked admin role to all permissions")


def downgrade() -> None:
    connection = op.get_bind()

    # Удаляем только роль с точным именем 'Admin', как и раньше
    connection.execute(sa.text("DELETE FROM role WHERE name='Admin'"))
    print("❌ Removed role with name 'Admin' (if it existed)")
