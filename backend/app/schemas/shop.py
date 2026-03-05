from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

from app.models.shop import ShopStatus


class ShopRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class ShopLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PriceItem(BaseModel):
    service: str
    price: float


class OpeningHours(BaseModel):
    mon: Optional[str] = None
    tue: Optional[str] = None
    wed: Optional[str] = None
    thu: Optional[str] = None
    fri: Optional[str] = None
    sat: Optional[str] = None
    sun: Optional[str] = None


class ShopProfileUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    opening_hours: Optional[dict] = None
    description: Optional[str] = None
    price_list: Optional[list[dict]] = None


class ShopStatusUpdate(BaseModel):
    status: ShopStatus
    wait_time: int


class ShopPublic(BaseModel):
    id: int
    name: str
    slug: str
    location: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    opening_hours: Optional[dict]
    photo_url: Optional[str]
    description: Optional[str]
    price_list: Optional[list]
    status: ShopStatus
    wait_time: int

    model_config = {"from_attributes": True}


class ShopPrivate(ShopPublic):
    email: str
    is_verified: bool
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    subscription_status: str
    created_at: datetime

    model_config = {"from_attributes": True}
