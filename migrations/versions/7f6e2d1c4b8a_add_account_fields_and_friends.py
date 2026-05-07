"""add account fields and friends

Revision ID: 7f6e2d1c4b8a
Revises: 8c4f2a1b9d3e
Create Date: 2026-05-07 14:36:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7f6e2d1c4b8a'
down_revision = '8c4f2a1b9d3e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('avatar', sa.String(length=255), nullable=True))

    op.create_table(
        'friend',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.Column('receiver_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['receiver_id'], ['user.id']),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sender_id', 'receiver_id', name='unique_friend')
    )


def downgrade():
    op.drop_table('friend')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('avatar')
