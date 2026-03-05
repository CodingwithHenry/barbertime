import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_shop
from app.core.upload import validate_image_bytes, delete_upload, UPLOAD_DIR, MAX_UPLOAD_BYTES
from app.models.employee import Employee
from app.models.shop import Shop
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeePublic
from app.services.queue_suggestion import suggest_wait_time, record_wait_time
from app.services.websocket_manager import manager

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("/", response_model=list[EmployeePublic])
async def list_employees(shop: Shop = Depends(get_current_shop), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.shop_id == shop.id))
    return result.scalars().all()


@router.post("/", response_model=EmployeePublic, status_code=201)
async def create_employee(
    body: EmployeeCreate,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    emp = Employee(shop_id=shop.id, name=body.name, role=body.role)
    db.add(emp)
    await db.commit()
    await db.refresh(emp)
    return emp


@router.patch("/{employee_id}", response_model=EmployeePublic)
async def update_employee(
    employee_id: int,
    body: EmployeeUpdate,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id, Employee.shop_id == shop.id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    old_wait = emp.wait_time
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(emp, field, value)
    await db.commit()
    await db.refresh(emp)

    if body.wait_time is not None and body.wait_time != old_wait:
        await record_wait_time(db, shop.id, body.wait_time, employee_id=emp.id)
        await manager.broadcast(shop.id, {
            "type": "employee_wait_update",
            "employee_id": emp.id,
            "wait_time": emp.wait_time,
        })
    return emp


@router.post("/{employee_id}/photo", response_model=EmployeePublic)
async def upload_employee_photo(
    employee_id: int,
    file: UploadFile = File(...),
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id, Employee.shop_id == shop.id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")
    validate_image_bytes(data)
    filename = f"{uuid.uuid4().hex}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, filename)
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)
    old_url = emp.photo_url
    emp.photo_url = f"/uploads/{filename}"
    await db.commit()
    await db.refresh(emp)
    delete_upload(old_url)
    return emp


@router.delete("/{employee_id}", status_code=204)
async def delete_employee(
    employee_id: int,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id, Employee.shop_id == shop.id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    await db.delete(emp)
    await db.commit()


@router.get("/{employee_id}/suggest-wait-time")
async def suggest_employee_wait(
    employee_id: int,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id, Employee.shop_id == shop.id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    suggestion = await suggest_wait_time(db, shop.id, emp.id)
    return {"suggested_wait_time": suggestion}
