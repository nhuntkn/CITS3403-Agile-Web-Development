"""add share table, friend table, and user avatar column

Revision ID: 182805b6caea
Revises: d0342b71b1ee
Create Date: 2026-05-05 14:32:24.518812

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '182805b6caea'
down_revision = 'd0342b71b1ee'
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
    op.create_table('friend',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('receiver_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(20), nullable=True),
    sa.ForeignKeyConstraint(['receiver_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('sender_id', 'receiver_id', name='unique_friend')
    )
    op.add_column('user', sa.Column('avatar', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('user', 'avatar')
    op.drop_table('friend')
    op.drop_table('share')
