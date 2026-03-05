from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_shop
from app.models.flash_discount import FlashDiscount
from app.models.shop import Shop
from app.schemas.flash_discount import FlashDiscountCreate, FlashDiscountUpdate, FlashDiscountPublic

router = APIRouter(prefix="/discounts", tags=["discounts"])


@router.get("/", response_model=list[FlashDiscountPublic])
async def list_discounts(shop: Shop = Depends(get_current_shop), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FlashDiscount).where(FlashDiscount.shop_id == shop.id))
    return result.scalars().all()


@router.post("/", response_model=FlashDiscountPublic, status_code=201)
async def create_discount(
    body: FlashDiscountCreate,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    discount = FlashDiscount(shop_id=shop.id, **body.model_dump())
    db.add(discount)
    await db.commit()
    await db.refresh(discount)
    return discount


@router.patch("/{discount_id}", response_model=FlashDiscountPublic)
async def update_discount(
    discount_id: int,
    body: FlashDiscountUpdate,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FlashDiscount).where(FlashDiscount.id == discount_id, FlashDiscount.shop_id == shop.id)
    )
    discount = result.scalar_one_or_none()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(discount, field, value)
    await db.commit()
    await db.refresh(discount)
    return discount


@router.post("/{discount_id}/redeem", response_model=FlashDiscountPublic)
async def redeem_discount(
    discount_id: int,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    # SELECT FOR UPDATE locks the row so concurrent redeems serialize
    result = await db.execute(
        select(FlashDiscount)
        .where(FlashDiscount.id == discount_id, FlashDiscount.shop_id == shop.id)
        .with_for_update()
    )
    discount = result.scalar_one_or_none()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    discount.uses_count += 1
    if discount.max_uses is not None and discount.uses_count >= discount.max_uses:
        discount.is_active = False
    await db.commit()
    await db.refresh(discount)
    return discount


@router.delete("/{discount_id}", status_code=204)
async def delete_discount(
    discount_id: int,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FlashDiscount).where(FlashDiscount.id == discount_id, FlashDiscount.shop_id == shop.id)
    )
    discount = result.scalar_one_or_none()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    await db.delete(discount)
    await db.commit()
