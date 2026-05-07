"""add share table

Revision ID: 182805b6caea
Revises: 7f6e2d1c4b8a
Create Date: 2026-05-05 14:32:24.518812

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '182805b6caea'
down_revision = '7f6e2d1c4b8a'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('share',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('receiver_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.Column('liked', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['session_id'], ['exercise_session.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('share')
