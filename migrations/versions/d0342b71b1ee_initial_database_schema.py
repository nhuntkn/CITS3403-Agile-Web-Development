"""initial database schema

Revision ID: d0342b71b1ee
Revises:
Create Date: 2026-05-02 19:00:58.481065

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd0342b71b1ee'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(50), nullable=False),
    sa.Column('password', sa.String(255), nullable=False),
    sa.Column('dob', sa.String(20), nullable=True),
    sa.Column('gender', sa.String(10), nullable=True),
    sa.Column('weight', sa.Float(), nullable=True),
    sa.Column('height', sa.Float(), nullable=True),
    sa.Column('calorie_goal', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('exercise_session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('date', sa.String(20), nullable=False),
    sa.Column('current_weight', sa.Float(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('total_calories', sa.Float(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('session_exercise',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('exercise_name', sa.String(50), nullable=False),
    sa.Column('activity_level', sa.String(50), nullable=False),
    sa.Column('minutes', sa.Integer(), nullable=False),
    sa.Column('met_value', sa.Float(), nullable=False),
    sa.Column('calories', sa.Float(), nullable=True),
    sa.Column('session_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['exercise_session.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('session_exercise')
    op.drop_table('exercise_session')
    op.drop_table('user')
