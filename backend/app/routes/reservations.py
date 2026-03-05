import re
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_shop
from app.models.reservation import Reservation, ReservationStatus
from app.models.shop import Shop
from app.schemas.reservation import ReservationCreate, ReservationPublic

router = APIRouter(prefix="/reservations", tags=["reservations"])

PHONE_RE = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def _normalize_phone(phone: str) -> str:
    return re.sub(r"[\s\-()]", "", phone)


@router.post("/{shop_id}", response_model=ReservationPublic, status_code=201)
async def create_reservation(
    shop_id: int,
    body: ReservationCreate,
    db: AsyncSession = Depends(get_db),
):
    if not PHONE_RE.match(body.phone_number):
        raise HTTPException(status_code=422, detail="Invalid phone number format")

    normalized = _normalize_phone(body.phone_number)

    # Advisory lock on phone hash prevents concurrent duplicate reservations
    # from both passing the rate-limit count check (TOCTOU race fix)
    phone_lock_key = hash(normalized) & 0x7FFFFFFFFFFFFFFF
    await db.execute(text(f"SELECT pg_advisory_xact_lock({phone_lock_key})"))

    # Rate limit: 1 active reservation per phone per day
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    existing = await db.execute(
        select(func.count(Reservation.id)).where(
            and_(
                Reservation.phone_number == normalized,
                Reservation.created_at >= today_start,
                Reservation.status == ReservationStatus.active,
            )
        )
    )
    count = existing.scalar_one()
    if count >= settings.RATE_LIMIT_RESERVATIONS_PER_DAY:
        raise HTTPException(status_code=429, detail="Reservation limit reached for today")

    # Verify shop exists and is open
    shop_result = await db.execute(select(Shop).where(Shop.id == shop_id, Shop.is_active == True))
    shop = shop_result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    if shop.status == "closed":
        raise HTTPException(status_code=400, detail="Shop is currently closed")

    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.RESERVATION_WINDOW_MINUTES)
    reservation = Reservation(
        shop_id=shop_id,
        employee_id=body.employee_id,
        phone_number=normalized,
        expires_at=expires_at,
    )
    db.add(reservation)
    await db.commit()
    await db.refresh(reservation)
    return reservation


@router.get("/", response_model=list[ReservationPublic])
async def list_reservations(
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    """Barber dashboard: view active reservations for their shop."""
    result = await db.execute(
        select(Reservation).where(
            Reservation.shop_id == shop.id,
            Reservation.status == ReservationStatus.active,
        ).order_by(Reservation.created_at)
    )
    return result.scalars().all()


@router.patch("/{reservation_id}/status", response_model=ReservationPublic)
async def update_reservation_status(
    reservation_id: int,
    new_status: ReservationStatus,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reservation).where(Reservation.id == reservation_id, Reservation.shop_id == shop.id)
    )
    res = result.scalar_one_or_none()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    res.status = new_status
    await db.commit()
    await db.refresh(res)
    return res
