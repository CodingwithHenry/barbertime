"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-05
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "shops",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("opening_hours", sa.JSON(), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price_list", sa.JSON(), nullable=True),
        sa.Column("status", sa.Enum("open", "busy", "closed", name="shopstatus"), nullable=False, server_default="closed"),
        sa.Column("wait_time", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("stripe_customer_id", sa.String(), nullable=True),
        sa.Column("stripe_subscription_id", sa.String(), nullable=True),
        sa.Column("subscription_status", sa.String(), nullable=False, server_default="inactive"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_shops_id", "shops", ["id"])
    op.create_index("ix_shops_email", "shops", ["email"], unique=True)
    op.create_index("ix_shops_slug", "shops", ["slug"], unique=True)

    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("wait_time", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index("ix_employees_id", "employees", ["id"])
    op.create_index("ix_employees_shop_id", "employees", ["shop_id"])

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("phone_number", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "expired", "cancelled", "honoured", name="reservationstatus"),
            nullable=False,
            server_default="active",
        ),
    )
    op.create_index("ix_reservations_id", "reservations", ["id"])
    op.create_index("ix_reservations_shop_id", "reservations", ["shop_id"])
    op.create_index("ix_reservations_phone_number", "reservations", ["phone_number"])

    op.create_table(
        "flash_discounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("uses_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_flash_discounts_id", "flash_discounts", ["id"])
    op.create_index("ix_flash_discounts_shop_id", "flash_discounts", ["shop_id"])

    op.create_table(
        "queue_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", sa.Integer(), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("wait_time", sa.Integer(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("hour_of_day", sa.Integer(), nullable=False),
    )
    op.create_index("ix_queue_history_id", "queue_history", ["id"])
    op.create_index("ix_queue_history_shop_id", "queue_history", ["shop_id"])
    op.create_index("ix_queue_history_employee_id", "queue_history", ["employee_id"])


def downgrade() -> None:
    op.drop_table("queue_history")
    op.drop_table("flash_discounts")
    op.drop_table("reservations")
    op.drop_table("employees")
    op.drop_table("shops")
    op.execute("DROP TYPE IF EXISTS shopstatus")
    op.execute("DROP TYPE IF EXISTS reservationstatus")
