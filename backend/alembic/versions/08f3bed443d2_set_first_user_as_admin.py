"""set_first_user_as_admin

Revision ID: 08f3bed443d2
Revises: 038bb220f8a5
Create Date: 2026-01-08

Story 1.1 AC-2: Data migration to set the first user (by created_at) as admin.
NOTE: If no users exist, this UPDATE affects 0 rows - expected behavior.
The registration endpoint handles the zero-admin case (Task 6).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08f3bed443d2'
down_revision: Union[str, None] = '038bb220f8a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Set the first user (by created_at) as admin (Story 1.1 AC-2)
    # If no users exist, this affects 0 rows - which is expected
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE users SET is_admin = TRUE
        WHERE id = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1)
    """))


def downgrade() -> None:
    # Reset all users to non-admin
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE users SET is_admin = FALSE
    """))
