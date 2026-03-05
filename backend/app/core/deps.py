from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.shop import Shop

bearer = HTTPBearer()


async def get_current_shop(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> Shop:
    shop_id = decode_token(credentials.credentials)
    if shop_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await db.execute(select(Shop).where(Shop.id == shop_id, Shop.is_active == True))
    shop = result.scalar_one_or_none()
    if shop is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Shop not found")
    return shop


async def get_current_subscribed_shop(shop: Shop = Depends(get_current_shop)) -> Shop:
    if shop.subscription_status not in ("active", "trialing"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Active subscription required",
        )
    return shop
