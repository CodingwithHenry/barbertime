"""Background task that expires reservations past their window and removes phone numbers at end of day."""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import update

from app.core.database import AsyncSessionLocal
from app.models.reservation import Reservation, ReservationStatus


async def expire_old_reservations() -> None:
    async with AsyncSessionLocal() as db:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Expire active reservations past their window
        await db.execute(
            update(Reservation)
            .where(
                Reservation.status == ReservationStatus.active,
                Reservation.expires_at < now,
            )
            .values(status=ReservationStatus.expired)
        )

        # Erase phone numbers from all reservations created before today
        # (rate-limit checks only look at today's reservations, so this is safe)
        await db.execute(
            update(Reservation)
            .where(
                Reservation.created_at < today_start,
                Reservation.phone_number != None,  # noqa: E711
            )
            .values(phone_number=None)
        )

        await db.commit()


async def run_cleanup_loop() -> None:
    while True:
        try:
            await expire_old_reservations()
        except Exception:
            pass
        await asyncio.sleep(60)  # run every minute
