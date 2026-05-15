"""add like_seen to share

Revision ID: a1b2c3d4e5f6
Revises: c09682e0d99f
Create Date: 2026-05-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c09682e0d99f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('share', schema=None) as batch_op:
        batch_op.add_column(sa.Column('like_seen', sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade():
    with op.batch_alter_table('share', schema=None) as batch_op:
        batch_op.drop_column('like_seen')
