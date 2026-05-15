"""add seen to share

Revision ID: 8a1f8e384e1e
Revises: f8794530dd25
Create Date: 2026-05-15 12:11:45.879946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a1f8e384e1e'
down_revision = 'f8794530dd25'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('share', schema=None) as batch_op:
        batch_op.add_column(sa.Column('seen', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade():
    with op.batch_alter_table('share', schema=None) as batch_op:
        batch_op.drop_column('seen')
