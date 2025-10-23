# Initial schema for H.O.M
from alembic import op
from app.db import engine
from sqlmodel import SQLModel

# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with engine.sync_engine.begin() as conn:
        SQLModel.metadata.create_all(bind=conn)

def downgrade():
    with engine.sync_engine.begin() as conn:
        SQLModel.metadata.drop_all(bind=conn)
