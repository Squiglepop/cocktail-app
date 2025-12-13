"""Add duplicate detection hash columns to recipes

Revision ID: add_dup_detect_001
Revises: fix_can_edit_001
Create Date: 2025-12-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = 'add_dup_detect_001'
down_revision: Union[str, None] = 'fix_can_edit_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    if 'recipes' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('recipes')]

        if 'image_content_hash' not in existing_columns:
            op.add_column('recipes', sa.Column('image_content_hash', sa.String(64), nullable=True))
            op.create_index('ix_recipes_image_content_hash', 'recipes', ['image_content_hash'])

        if 'image_perceptual_hash' not in existing_columns:
            op.add_column('recipes', sa.Column('image_perceptual_hash', sa.String(16), nullable=True))
            op.create_index('ix_recipes_image_perceptual_hash', 'recipes', ['image_perceptual_hash'])

        if 'recipe_fingerprint' not in existing_columns:
            op.add_column('recipes', sa.Column('recipe_fingerprint', sa.String(32), nullable=True))
            op.create_index('ix_recipes_recipe_fingerprint', 'recipes', ['recipe_fingerprint'])


def downgrade() -> None:
    op.drop_index('ix_recipes_recipe_fingerprint', table_name='recipes')
    op.drop_column('recipes', 'recipe_fingerprint')
    op.drop_index('ix_recipes_image_perceptual_hash', table_name='recipes')
    op.drop_column('recipes', 'image_perceptual_hash')
    op.drop_index('ix_recipes_image_content_hash', table_name='recipes')
    op.drop_column('recipes', 'image_content_hash')
