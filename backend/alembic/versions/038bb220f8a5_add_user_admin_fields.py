"""add_user_admin_fields

Revision ID: 038bb220f8a5
Revises: db43d35b27a2
Create Date: 2026-01-08

Story 1.1: Add is_admin and last_login_at fields to users table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '038bb220f8a5'
down_revision: Union[str, None] = 'db43d35b27a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_admin column with default false (Story 1.1 AC-1)
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'))
    # Add last_login_at column, nullable since users may not have logged in yet (Story 1.1 AC-1)
    op.add_column('users', sa.Column('last_login_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'last_login_at')
    op.drop_column('users', 'is_admin')
