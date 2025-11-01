"""init tables safely + seed default roles, permissions, and admin links

Revision ID: 0001_init
Revises: 
Create Date: 2025-11-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Core tables
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    op.create_table(
        "role",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("description", sa.String(), nullable=True),
    )

    op.create_table(
        "permission",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), unique=True, nullable=False),
        sa.Column("description", sa.String(), nullable=True),
    )

    op.create_table(
        "admin_menu_link",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("icon", sa.String(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )

    # --- Association tables
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permission.id", ondelete="CASCADE"), primary_key=True),
    )

    # --- Seed defaults (idempotent)
    conn = op.get_bind()

    # Roles
    sql_roles = sa.text(
        "INSERT INTO role (name, description) "
        "VALUES (:name, :desc) "
        "ON CONFLICT (name) DO NOTHING"
    )
    conn.execute(
        sql_roles,
        [{"name": "admin", "desc": "Администратор"}, {"name": "user", "desc": "Пользователь"}],
    )

    # Permissions
    perm_names = [
        ("admin_access", "Доступ в админ-панель"),
        ("manage_users", "Управление пользователями"),
        ("manage_roles", "Управление ролями"),
        ("view_dashboard", "Просмотр дашборда"),
    ]
    sql_perms = sa.text(
        "INSERT INTO permission (name, description) "
        "VALUES (:name, :desc) "
        "ON CONFLICT (name) DO NOTHING"
    )
    conn.execute(sql_perms, [{"name": n, "desc": d} for n, d in perm_names])

    # Grant admin permissions
    sql_grant = sa.text(
        "INSERT INTO role_permissions (role_id, permission_id) "
        "SELECT r.id, p.id "
        "FROM role r CROSS JOIN permission p "
        "WHERE r.name='admin' "
        "AND p.name IN ('admin_access','manage_users','manage_roles','view_dashboard') "
        "ON CONFLICT DO NOTHING"
    )
    conn.execute(sql_grant)

    # Admin menu links
    sql_links = sa.text(
        "INSERT INTO admin_menu_link (title, url, icon, \"order\") "
        "VALUES (:title, :url, :icon, :ord) "
        "ON CONFLICT DO NOTHING"
    )
    links = [
        ("Панель", "/adminpanel", "layout-dashboard"),
        ("Пользователи", "/adminpanel/users", "users"),
        ("Роли", "/adminpanel/roles", "shield"),
    ]
    for idx, (title, url, icon) in enumerate(links):
        conn.execute(sql_links, {"title": title, "url": url, "icon": icon, "ord": idx})


def downgrade() -> None:
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("admin_menu_link")
    op.drop_table("permission")
    op.drop_table("role")
    op.drop_table("user")
