"""Add image data storage to recipes

Revision ID: add_image_storage_001
Revises: add_user_auth_001
Create Date: 2025-12-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_image_storage_001'
down_revision: Union[str, None] = 'add_user_auth_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add image data columns to recipes table using batch mode for SQLite compatibility
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_image_data', sa.LargeBinary, nullable=True))
        batch_op.add_column(sa.Column('source_image_mime', sa.String(50), nullable=True))


def downgrade() -> None:
    # Remove image data columns using batch mode
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.drop_column('source_image_mime')
        batch_op.drop_column('source_image_data')
