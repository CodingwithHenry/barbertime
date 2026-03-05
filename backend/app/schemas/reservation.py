from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.reservation import ReservationStatus


class ReservationCreate(BaseModel):
    phone_number: str
    employee_id: Optional[int] = None


class ReservationPublic(BaseModel):
    id: int
    shop_id: int
    employee_id: Optional[int]
    expires_at: datetime
    status: ReservationStatus

    model_config = {"from_attributes": True}
