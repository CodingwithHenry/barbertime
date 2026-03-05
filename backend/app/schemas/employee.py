from typing import Optional
from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    name: str
    role: Optional[str] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    wait_time: Optional[int] = None
    is_active: Optional[bool] = None


class EmployeePublic(BaseModel):
    id: int
    shop_id: int
    name: str
    photo_url: Optional[str]
    role: Optional[str]
    wait_time: int
    is_active: bool

    model_config = {"from_attributes": True}
