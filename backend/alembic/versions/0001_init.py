"""init tables safely + seed default roles, permissions, and admin links"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # === Permission table ===
    if "permission" not in inspector.get_table_names():
        op.create_table(
            "permission",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("code", sa.String(100), nullable=False, unique=True, index=True),
            sa.Column("description", sa.String(255)),
        )

    # === Role table ===
    if "role" not in inspector.get_table_names():
        op.create_table(
            "role",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True, index=True),
            sa.Column("description", sa.String(255)),
        )

    # === User table ===
    if "user" not in inspector.get_table_names():
        op.create_table(
            "user",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String(255), nullable=False, unique=True, index=True),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("is_active", sa.Boolean, server_default=sa.text("TRUE"), nullable=False),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # === Link table: user_role_link ===
    if "user_role_link" not in inspector.get_table_names():
        op.create_table(
            "user_role_link",
            sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("role_id", sa.Integer, sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
        )

    # === Link table: role_permission_link ===
    if "role_permission_link" not in inspector.get_table_names():
        op.create_table(
            "role_permission_link",
            sa.Column("role_id", sa.Integer, sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("permission_id", sa.Integer, sa.ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
        )

    # === SEED default roles and permissions ===
    connection = op.get_bind()

    # Existing roles
    existing_roles = []
    if "role" in inspector.get_table_names():
        existing_roles = [r[0] for r in connection.execute(sa.text("SELECT name FROM role")).fetchall()]

    # Insert roles
    if "admin" not in existing_roles:
        connection.execute(
            sa.text("INSERT INTO role (name, description) VALUES (:name, :desc)"),
            {"name": "admin", "desc": "Administrator role"},
        )

    if "user" not in existing_roles:
        connection.execute(
            sa.text("INSERT INTO role (name, description) VALUES (:name, :desc)"),
            {"name": "user", "desc": "Default user role"},
        )

    # Existing permissions
    existing_permissions = []
    if "permission" in inspector.get_table_names():
        existing_permissions = [p[0] for p in connection.execute(sa.text("SELECT code FROM permission")).fetchall()]

    default_permissions = [
        {"code": "view_dashboard", "description": "Access to dashboard"},
        {"code": "manage_users", "description": "Can manage users"},
        {"code": "manage_roles", "description": "Can manage roles"},
    ]

    for perm in default_permissions:
        if perm["code"] not in existing_permissions:
            connection.execute(
                sa.text("INSERT INTO permission (code, description) VALUES (:code, :desc)"),
                {"code": perm["code"], "desc": perm["description"]},
            )

    # === Link admin role with all permissions ===
    admin_role_id = connection.execute(sa.text("SELECT id FROM role WHERE name = 'admin'")).scalar()
    if admin_role_id:
        permissions = connection.execute(sa.text("SELECT id FROM permission")).fetchall()
        for (perm_id,) in permissions:
            exists = connection.execute(
                sa.text("SELECT 1 FROM role_permission_link WHERE role_id = :r AND permission_id = :p"),
                {"r": admin_role_id, "p": perm_id},
            ).fetchone()
            if not exists:
                connection.execute(
                    sa.text("INSERT INTO role_permission_link (role_id, permission_id) VALUES (:r, :p)"),
                    {"r": admin_role_id, "p": perm_id},
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Drop in reverse dependency order
    if "role_permission_link" in inspector.get_table_names():
        op.drop_table("role_permission_link")

    if "user_role_link" in inspector.get_table_names():
        op.drop_table("user_role_link")

    if "user" in inspector.get_table_names():
        op.drop_table("user")

    if "role" in inspector.get_table_names():
        op.drop_table("role")

    if "permission" in inspector.get_table_names():
        op.drop_table("permission")
