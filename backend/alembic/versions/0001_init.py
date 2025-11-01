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

    # === Role table ===
    if "role" not in inspector.get_table_names():
        op.create_table(
            "role",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String, unique=True, nullable=False),
            sa.Column("description", sa.String),
        )

    # === User table ===
    if "user" not in inspector.get_table_names():
        op.create_table(
            "user",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.String, unique=True, nullable=False),
            sa.Column("password_hash", sa.String(255), nullable=False),
            sa.Column("role_id", sa.Integer, sa.ForeignKey("role.id")),
        )

    # === Any other tables (examples) ===
    if "session" not in inspector.get_table_names():
        op.create_table(
            "session",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id")),
            sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # === Session table ===
    if "session" in inspector.get_table_names():
        op.drop_table("session")

    # === User table ===
    if "user" in inspector.get_table_names():
        op.drop_table("user")

    # === Role table ===
    if "role" in inspector.get_table_names():
        op.drop_table("role")
