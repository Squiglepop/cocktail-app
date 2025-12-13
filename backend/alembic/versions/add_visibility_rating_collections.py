"""Add visibility, rating, and collections

Revision ID: add_vis_rating_coll_001
Revises: add_image_storage_001
Create Date: 2025-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_vis_rating_coll_001'
down_revision: Union[str, None] = 'add_image_storage_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add visibility and rating columns to recipes table
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('visibility', sa.String(20), nullable=False, server_default='public')
        )
        batch_op.add_column(
            sa.Column('rating', sa.Integer, nullable=True)
        )
        batch_op.create_index('ix_recipes_visibility', ['visibility'])

    # Create collections table
    op.create_table(
        'collections',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('is_public', sa.Boolean, nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_collections_name', 'collections', ['name'])
    op.create_index('ix_collections_user_id', 'collections', ['user_id'])

    # Create collection_recipes junction table
    op.create_table(
        'collection_recipes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('collection_id', sa.String(36), sa.ForeignKey('collections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('position', sa.Integer, nullable=False, server_default='0'),
        sa.Column('added_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_collection_recipes_collection_id', 'collection_recipes', ['collection_id'])
    op.create_index('ix_collection_recipes_recipe_id', 'collection_recipes', ['recipe_id'])


def downgrade() -> None:
    # Drop collection_recipes table
    op.drop_index('ix_collection_recipes_recipe_id', table_name='collection_recipes')
    op.drop_index('ix_collection_recipes_collection_id', table_name='collection_recipes')
    op.drop_table('collection_recipes')

    # Drop collections table
    op.drop_index('ix_collections_user_id', table_name='collections')
    op.drop_index('ix_collections_name', table_name='collections')
    op.drop_table('collections')

    # Remove visibility and rating columns from recipes
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.drop_index('ix_recipes_visibility')
        batch_op.drop_column('rating')
        batch_op.drop_column('visibility')
