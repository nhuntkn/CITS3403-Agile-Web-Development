"""add location to exercise session

Revision ID: 8c4f2a1b9d3e
Revises: d0342b71b1ee
Create Date: 2026-05-06 14:39:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c4f2a1b9d3e'
down_revision = 'd0342b71b1ee'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('exercise_session', schema=None) as batch_op:
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('exercise_session', schema=None) as batch_op:
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')
