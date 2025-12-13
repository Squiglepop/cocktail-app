"""Add user_ratings table and migrate existing ratings

Revision ID: add_user_ratings_001
Revises: add_vis_rating_coll_001
Create Date: 2025-12-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_user_ratings_001'
down_revision: Union[str, None] = 'add_vis_rating_coll_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_ratings table
    op.create_table(
        'user_ratings',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipe_id', sa.String(36), sa.ForeignKey('recipes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
    )
    op.create_index('ix_user_ratings_user_id', 'user_ratings', ['user_id'])
    op.create_index('ix_user_ratings_recipe_id', 'user_ratings', ['recipe_id'])
    op.create_unique_constraint('uq_user_rating', 'user_ratings', ['user_id', 'recipe_id'])

    # Migrate existing ratings from recipes table to user_ratings
    # Only migrate recipes that have both a user_id and a rating
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO user_ratings (id, user_id, recipe_id, rating, created_at, updated_at)
        SELECT
            lower(hex(randomblob(4)) || '-' || hex(randomblob(2)) || '-4' ||
                  substr(hex(randomblob(2)), 2) || '-' ||
                  substr('89ab', abs(random()) % 4 + 1, 1) ||
                  substr(hex(randomblob(2)), 2) || '-' || hex(randomblob(6))),
            user_id,
            id,
            rating,
            created_at,
            updated_at
        FROM recipes
        WHERE user_id IS NOT NULL AND rating IS NOT NULL
    """))

    # Drop the rating column from recipes table
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.drop_column('rating')


def downgrade() -> None:
    # Re-add rating column to recipes
    with op.batch_alter_table('recipes', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('rating', sa.Integer, nullable=True)
        )

    # Migrate ratings back to recipes (only for recipe owners)
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE recipes
        SET rating = (
            SELECT ur.rating
            FROM user_ratings ur
            WHERE ur.recipe_id = recipes.id
            AND ur.user_id = recipes.user_id
        )
        WHERE user_id IS NOT NULL
    """))

    # Drop user_ratings table
    op.drop_constraint('uq_user_rating', 'user_ratings', type_='unique')
    op.drop_index('ix_user_ratings_recipe_id', table_name='user_ratings')
    op.drop_index('ix_user_ratings_user_id', table_name='user_ratings')
    op.drop_table('user_ratings')
