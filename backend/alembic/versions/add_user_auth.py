"""Add user authentication tables

Revision ID: add_user_auth_001
Revises: 0dda6df88568
Create Date: 2025-12-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_user_auth_001'
down_revision: Union[str, None] = '0dda6df88568'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Add user_id column to recipes table using batch mode for SQLite compatibility
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(36), nullable=True))
        batch_op.create_index('ix_recipes_user_id', ['user_id'])
        batch_op.create_foreign_key(
            'fk_recipes_user_id_users',
            'users',
            ['user_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    # Remove user_id column from recipes using batch mode
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.drop_constraint('fk_recipes_user_id_users', type_='foreignkey')
        batch_op.drop_index('ix_recipes_user_id')
        batch_op.drop_column('user_id')

    # Drop users table
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
