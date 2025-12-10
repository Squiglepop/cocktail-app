"""Initial migration - create all tables

Revision ID: 0dda6df88568
Revises:
Create Date: 2025-12-09 14:29:48.891052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0dda6df88568'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create recipes table
    op.create_table(
        'recipes',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('instructions', sa.Text, nullable=True),
        sa.Column('template', sa.String(50), nullable=True, index=True),
        sa.Column('main_spirit', sa.String(50), nullable=True, index=True),
        sa.Column('glassware', sa.String(50), nullable=True, index=True),
        sa.Column('serving_style', sa.String(50), nullable=True, index=True),
        sa.Column('method', sa.String(50), nullable=True, index=True),
        sa.Column('source_image_path', sa.String(512), nullable=True),
        sa.Column('source_url', sa.String(512), nullable=True),
        sa.Column('source_type', sa.String(50), nullable=True),
        sa.Column('garnish', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )

    # Create ingredients table
    op.create_table(
        'ingredients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('type', sa.String(50), nullable=False, index=True),
        sa.Column('spirit_category', sa.String(50), nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('common_brands', sa.Text, nullable=True),
    )

    # Create recipe_ingredients junction table
    op.create_table(
        'recipe_ingredients',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ingredient_id', sa.String(36), sa.ForeignKey('ingredients.id'), nullable=False),
        sa.Column('amount', sa.Float, nullable=True),
        sa.Column('unit', sa.String(20), nullable=True),
        sa.Column('notes', sa.String(255), nullable=True),
        sa.Column('optional', sa.Boolean, nullable=False, default=False),
        sa.Column('order', sa.Integer, nullable=False, default=0),
    )

    # Create extraction_jobs table
    op.create_table(
        'extraction_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('status', sa.String(50), nullable=False, default='pending'),
        sa.Column('image_path', sa.String(512), nullable=False),
        sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('raw_extraction', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('completed_at', sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table('extraction_jobs')
    op.drop_table('recipe_ingredients')
    op.drop_table('ingredients')
    op.drop_table('recipes')
