"""create_audit_log_table

Revision ID: f2c3f52ad94e
Revises: 4557012699e7
Create Date: 2026-04-09 19:50:29.673247

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2c3f52ad94e'
down_revision: Union[str, None] = '4557012699e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('admin_audit_log',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('admin_user_id', sa.String(length=36), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('entity_type', sa.String(length=50), nullable=False),
    sa.Column('entity_id', sa.String(length=36), nullable=True),
    sa.Column('details', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['admin_user_id'], ['users.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_audit_log_action'), 'admin_audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_admin_audit_log_created_at'), 'admin_audit_log', ['created_at'], unique=False)
    op.create_index(op.f('ix_admin_audit_log_entity_type'), 'admin_audit_log', ['entity_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_admin_audit_log_entity_type'), table_name='admin_audit_log')
    op.drop_index(op.f('ix_admin_audit_log_created_at'), table_name='admin_audit_log')
    op.drop_index(op.f('ix_admin_audit_log_action'), table_name='admin_audit_log')
    op.drop_table('admin_audit_log')
