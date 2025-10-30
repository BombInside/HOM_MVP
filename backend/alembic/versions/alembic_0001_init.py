python
"""init explicit tables"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_init_explicit"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "role",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True, index=True),
        sa.Column("description", sa.String, nullable=True),
    )

    op.create_table(
        "user",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True, index=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "userrolelink",
        sa.Column("user_id", sa.Integer, sa.ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("role.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "line",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False, unique=True, index=True),
        sa.Column("is_deleted", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "machine",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("line_id", sa.Integer, sa.ForeignKey("line.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("name", sa.String, nullable=False, index=True),
        sa.Column("is_deleted", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "repair",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("machine_id", sa.Integer, sa.ForeignKey("machine.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("started_at", sa.TIMESTAMP(timezone=False), server_default=sa.text("now()"), nullable=False, index=True),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=False), nullable=True),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("is_deleted", sa.Boolean, server_default=sa.text("false"), nullable=False, index=True),
    )

    op.create_table(
        "auditlog",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("entity", sa.String, nullable=False),
        sa.Column("entity_id", sa.String, nullable=False),
        sa.Column("action", sa.String, nullable=False),
        sa.Column("performed_by", sa.Integer, sa.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("at", sa.TIMESTAMP(timezone=False), server_default=sa.text("now()"), nullable=False, index=True),
        sa.Column("diff", sa.JSON, nullable=True),
    )


def downgrade():
    for name in ("auditlog", "repair", "machine", "line", "userrolelink", "user", "role"):
        op.drop_table(name)
