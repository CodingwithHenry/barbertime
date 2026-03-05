"""Make reservation phone_number nullable for end-of-day anonymisation

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-05
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("reservations", "phone_number", nullable=True)


def downgrade() -> None:
    op.alter_column("reservations", "phone_number", nullable=False)
