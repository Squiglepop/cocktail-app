"""add_ingredient_id_index

Revision ID: 4557012699e7
Revises: 5cfe7a74576e
Create Date: 2026-01-30 10:48:16.797553

Story 1.4 AC-4: Add index on recipe_ingredients.ingredient_id for query performance.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4557012699e7'
down_revision: Union[str, None] = '5cfe7a74576e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        'ix_recipe_ingredients_ingredient_id',
        'recipe_ingredients',
        ['ingredient_id'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_recipe_ingredients_ingredient_id', table_name='recipe_ingredients')
