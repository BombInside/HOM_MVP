"""init tables safely"""

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
