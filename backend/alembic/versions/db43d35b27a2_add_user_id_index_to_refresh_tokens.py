"""add_user_id_index_to_refresh_tokens

Revision ID: db43d35b27a2
Revises: b1e016e6f80c
Create Date: 2025-12-31 01:36:01.051678

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db43d35b27a2'
down_revision: Union[str, None] = 'b1e016e6f80c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Story 0.2 Code Review: Add missing user_id index for revoke_all_user_tokens performance
    op.create_index(
        op.f('ix_refresh_tokens_user_id'),
        'refresh_tokens',
        ['user_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
