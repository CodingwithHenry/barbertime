"""Add email verification: is_verified on shops, verification_codes table

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-05
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Existing shops are considered verified
    op.add_column("shops", sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="true"))

    op.create_table(
        "verification_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("code", sa.String(6), nullable=False),
        sa.Column("purpose", sa.Enum("email_verify", "password_reset", name="verificationpurpose"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_verification_codes_email", "verification_codes", ["email"])


def downgrade() -> None:
    op.drop_index("ix_verification_codes_email", "verification_codes")
    op.drop_table("verification_codes")
    op.drop_column("shops", "is_verified")
    op.execute("DROP TYPE IF EXISTS verificationpurpose")
