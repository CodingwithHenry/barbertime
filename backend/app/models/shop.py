import enum
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ShopStatus(str, enum.Enum):
    open = "open"
    busy = "busy"
    closed = "closed"


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    opening_hours: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_list: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ShopStatus] = mapped_column(Enum(ShopStatus), default=ShopStatus.closed, nullable=False)
    wait_time: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String, nullable=True)
    subscription_status: Mapped[str] = mapped_column(String, default="inactive", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    employees: Mapped[list["Employee"]] = relationship("Employee", back_populates="shop", cascade="all, delete-orphan")
    reservations: Mapped[list["Reservation"]] = relationship("Reservation", back_populates="shop", cascade="all, delete-orphan")
    flash_discounts: Mapped[list["FlashDiscount"]] = relationship("FlashDiscount", back_populates="shop", cascade="all, delete-orphan")
    queue_history: Mapped[list["QueueHistory"]] = relationship("QueueHistory", back_populates="shop", cascade="all, delete-orphan")
