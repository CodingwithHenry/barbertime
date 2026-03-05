from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FlashDiscountCreate(BaseModel):
    title: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None


class FlashDiscountUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    is_active: Optional[bool] = None


class FlashDiscountPublic(BaseModel):
    id: int
    shop_id: int
    title: str
    description: Optional[str]
    expires_at: Optional[datetime]
    max_uses: Optional[int]
    uses_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
