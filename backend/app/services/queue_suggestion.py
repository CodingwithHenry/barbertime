from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.queue_history import QueueHistory


async def suggest_wait_time(
    db: AsyncSession,
    shop_id: int,
    employee_id: Optional[int] = None,
) -> Optional[int]:
    """Return average wait time for same day-of-week + hour over last 4 weeks, or None."""
    now = datetime.now(timezone.utc)
    four_weeks_ago = now - timedelta(weeks=4)

    query = (
        select(func.avg(QueueHistory.wait_time))
        .where(
            QueueHistory.shop_id == shop_id,
            QueueHistory.recorded_at >= four_weeks_ago,
            QueueHistory.day_of_week == now.weekday(),
            QueueHistory.hour_of_day == now.hour,
        )
    )
    if employee_id is not None:
        query = query.where(QueueHistory.employee_id == employee_id)

    result = await db.execute(query)
    avg = result.scalar_one_or_none()
    if avg is None:
        return None
    return int(round(avg))


async def record_wait_time(
    db: AsyncSession,
    shop_id: int,
    wait_time: int,
    employee_id: Optional[int] = None,
) -> None:
    now = datetime.now(timezone.utc)
    entry = QueueHistory(
        shop_id=shop_id,
        employee_id=employee_id,
        wait_time=wait_time,
        recorded_at=now,
        day_of_week=now.weekday(),
        hour_of_day=now.hour,
    )
    db.add(entry)
    await db.commit()
