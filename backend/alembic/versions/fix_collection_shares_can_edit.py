"""Fix collection_shares missing can_edit column

Revision ID: fix_can_edit_001
Revises: add_collection_shares_001
Create Date: 2025-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'fix_can_edit_001'
down_revision: Union[str, None] = 'add_collection_shares_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    if 'collection_shares' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('collection_shares')]
        if 'can_edit' not in existing_columns:
            op.add_column('collection_shares', sa.Column('can_edit', sa.Boolean, nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('collection_shares', 'can_edit')
