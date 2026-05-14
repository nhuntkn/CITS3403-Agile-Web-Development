"""add email column to user

Revision ID: f8794530dd25
Revises: 3118966b9573
Create Date: 2026-05-12 12:28:41.647881

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8794530dd25'
down_revision = '3118966b9573'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'user',
        sa.Column('email', sa.String(length=120), nullable=True)
    )


def downgrade():
    op.drop_column('user', 'email')
