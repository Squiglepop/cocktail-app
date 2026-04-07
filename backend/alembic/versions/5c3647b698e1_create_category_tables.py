"""create_category_tables

Revision ID: 5c3647b698e1
Revises: 08f3bed443d2
Create Date: 2026-01-30 10:46:08.224011

Story 1.4 AC-1: Create the 5 category database tables to replace Python enums.
Tables: category_templates, category_glassware, category_serving_styles,
        category_methods, category_spirits
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c3647b698e1'
down_revision: Union[str, None] = '08f3bed443d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # category_templates table
    op.create_table(
        'category_templates',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('value', sa.String(50), unique=True, nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_category_templates_value', 'category_templates', ['value'])

    # category_glassware table
    op.create_table(
        'category_glassware',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('value', sa.String(50), unique=True, nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_category_glassware_value', 'category_glassware', ['value'])

    # category_serving_styles table
    op.create_table(
        'category_serving_styles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('value', sa.String(50), unique=True, nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_category_serving_styles_value', 'category_serving_styles', ['value'])

    # category_methods table
    op.create_table(
        'category_methods',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('value', sa.String(50), unique=True, nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_category_methods_value', 'category_methods', ['value'])

    # category_spirits table
    op.create_table(
        'category_spirits',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('value', sa.String(50), unique=True, nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('sort_order', sa.Integer(), default=0, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_category_spirits_value', 'category_spirits', ['value'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_category_spirits_value', table_name='category_spirits')
    op.drop_table('category_spirits')

    op.drop_index('ix_category_methods_value', table_name='category_methods')
    op.drop_table('category_methods')

    op.drop_index('ix_category_serving_styles_value', table_name='category_serving_styles')
    op.drop_table('category_serving_styles')

    op.drop_index('ix_category_glassware_value', table_name='category_glassware')
    op.drop_table('category_glassware')

    op.drop_index('ix_category_templates_value', table_name='category_templates')
    op.drop_table('category_templates')
