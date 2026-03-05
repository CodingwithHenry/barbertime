"""Replace name-based slugs with UUIDs

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace existing name-based slugs with UUIDs
    op.execute(
        "UPDATE shops SET slug = gen_random_uuid()::text "
        "WHERE slug !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'"
    )


def downgrade() -> None:
    pass
