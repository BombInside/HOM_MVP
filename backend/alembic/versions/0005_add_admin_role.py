"""Add admin role and full permissions"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean, ForeignKey, select
from datetime import datetime

# revision identifiers, used by Alembic.
revision = "0005_seed_admin_role"
down_revision = "0004_add_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()

    # Define tables (lightweight version)
    role_table = table(
        "role",
        column("id", Integer),
        column("name", String),
        column("description", String),
    )

    permission_table = table(
        "permission",
        column("id", Integer),
        column("name", String),
        column("description", String),
    )

    link_table = None
    try:
        link_table = table(
            "role_permission_link",
            column("role_id", Integer),
            column("permission_id", Integer),
        )
    except Exception:
        # If no linking table, skip linking step
        pass

    # 1️⃣  Ensure Admin role exists
    existing_roles = connection.execute(sa.text("SELECT id FROM role WHERE name = 'Admin'")).fetchall()
    if not existing_roles:
        connection.execute(
            sa.text("INSERT INTO role (name, description) VALUES (:name, :desc)"),
            {"name": "Admin", "desc": "Full access to all features"},
        )
        print("✅ Created Admin role")
    else:
        print("ℹ️ Admin role already exists")

    # 2️⃣  Ensure permissions exist
    existing_perms = []
    try:
        existing_perms = [r[0] for r in connection.execute(sa.text("SELECT name FROM permission")).fetchall()]
    except Exception:
        print("⚠️ No permission table found, skipping permission creation.")

    default_perms = [
        ("view", "View access"),
        ("create", "Create access"),
        ("edit", "Edit access"),
        ("delete", "Delete access"),
        ("manage_users", "Manage users"),
        ("manage_roles", "Manage roles"),
        ("manage_settings", "Manage application settings"),
    ]

    for name, desc in default_perms:
        if name not in existing_perms:
            try:
                connection.execute(
                    sa.text("INSERT INTO permission (name, description) VALUES (:n, :d)"),
                    {"n": name, "d": desc},
                )
                print(f"✅ Created permission: {name}")
            except Exception:
                pass

    # 3️⃣  Link Admin to all permissions
    if link_table is not None:
        admin_id = connection.execute(sa.text("SELECT id FROM role WHERE name = 'Admin'")).scalar()
        if admin_id:
            perm_ids = [r[0] for r in connection.execute(sa.text("SELECT id FROM permission")).fetchall()]
            for pid in perm_ids:
                exists = connection.execute(
                    sa.text(
                        "SELECT 1 FROM role_permission_link WHERE role_id=:r AND permission_id=:p"
                    ),
                    {"r": admin_id, "p": pid},
                ).fetchone()
                if not exists:
                    connection.execute(
                        sa.text(
                            "INSERT INTO role_permission_link (role_id, permission_id) VALUES (:r, :p)"
                        ),
                        {"r": admin_id, "p": pid},
                    )
            print("✅ Linked Admin to all permissions")


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM role WHERE name='Admin'"))
    print("❌ Removed Admin role")
