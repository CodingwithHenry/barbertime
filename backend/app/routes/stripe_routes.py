from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_shop
from app.models.shop import Shop
from app.services import stripe_service

router = APIRouter(prefix="/stripe", tags=["stripe"])


@router.post("/subscribe")
async def subscribe(
    plan: Literal["monthly", "yearly"] = Query(...),
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    if shop.subscription_status in ("active", "trialing"):
        raise HTTPException(status_code=400, detail="Already subscribed")

    if not shop.stripe_customer_id:
        customer_id = await stripe_service.create_customer(shop)
        shop.stripe_customer_id = customer_id
        await db.commit()

    price_id = (
        settings.STRIPE_PRICE_ID_MONTHLY if plan == "monthly"
        else settings.STRIPE_PRICE_ID_YEARLY
    )
    url = await stripe_service.create_checkout_session(
        customer_id=shop.stripe_customer_id,
        price_id=price_id,
        success_url=f"{settings.FRONTEND_URL}/dashboard/subscription?success=1",
        cancel_url=f"{settings.FRONTEND_URL}/dashboard/subscription",
    )
    return {"url": url}


@router.get("/portal")
async def billing_portal(
    shop: Shop = Depends(get_current_shop),
):
    if not shop.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing account found")
    url = await stripe_service.create_portal_session(
        shop.stripe_customer_id,
        return_url=f"{settings.FRONTEND_URL}/dashboard/subscription",
    )
    return {"url": url}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        await stripe_service.handle_webhook_event(payload, sig_header, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "ok"}
