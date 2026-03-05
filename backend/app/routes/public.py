from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.models.shop import Shop
from app.models.employee import Employee
from app.models.flash_discount import FlashDiscount
from app.schemas.shop import ShopPublic
from app.schemas.employee import EmployeePublic
from app.schemas.flash_discount import FlashDiscountPublic

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/shops", response_model=list[ShopPublic])
async def list_shops(
    lat: float | None = None,
    lon: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Shop).where(
            Shop.is_active == True,
            Shop.subscription_status.in_(["active", "trialing"]),
        )
    )
    shops = result.scalars().all()

    # Sort by proximity if coordinates provided
    if lat is not None and lon is not None:
        def distance(s: Shop):
            if s.latitude is None or s.longitude is None:
                return float("inf")
            return (s.latitude - lat) ** 2 + (s.longitude - lon) ** 2

        shops = sorted(shops, key=distance)

    return shops


@router.get("/shops/{slug}", response_model=ShopPublic)
async def get_shop(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.slug == slug, Shop.is_active == True))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop


@router.get("/shops/{slug}/employees", response_model=list[EmployeePublic])
async def get_shop_employees(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.slug == slug, Shop.is_active == True))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    emp_result = await db.execute(
        select(Employee).where(Employee.shop_id == shop.id, Employee.is_active == True)
    )
    return emp_result.scalars().all()


@router.get("/shops/{slug}/discounts", response_model=list[FlashDiscountPublic])
async def get_shop_discounts(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shop).where(Shop.slug == slug, Shop.is_active == True))
    shop = result.scalar_one_or_none()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    now = datetime.now(timezone.utc)
    disc_result = await db.execute(
        select(FlashDiscount).where(
            FlashDiscount.shop_id == shop.id,
            FlashDiscount.is_active == True,
            and_(
                (FlashDiscount.expires_at == None) | (FlashDiscount.expires_at > now)
            ),
        )
    )
    discounts = disc_result.scalars().all()

    # Filter out exhausted discounts
    return [d for d in discounts if d.max_uses is None or d.uses_count < d.max_uses]
