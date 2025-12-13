"""Add collection_shares table for playlist sharing

Revision ID: add_collection_shares_001
Revises: add_user_ratings_001
Create Date: 2025-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_collection_shares_001'
down_revision: Union[str, None] = 'add_user_ratings_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create collection_shares table with unique constraint inline (SQLite compatible)
    op.create_table(
        'collection_shares',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('collection_id', sa.String(36), sa.ForeignKey('collections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('shared_with_user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('can_edit', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('shared_at', sa.DateTime, nullable=False),
        sa.UniqueConstraint('collection_id', 'shared_with_user_id', name='uq_collection_share'),
    )
    op.create_index('ix_collection_shares_collection_id', 'collection_shares', ['collection_id'])
    op.create_index('ix_collection_shares_shared_with_user_id', 'collection_shares', ['shared_with_user_id'])


def downgrade() -> None:
    # Drop collection_shares table (constraint dropped with table)
    op.drop_index('ix_collection_shares_shared_with_user_id', table_name='collection_shares')
    op.drop_index('ix_collection_shares_collection_id', table_name='collection_shares')
    op.drop_table('collection_shares')
