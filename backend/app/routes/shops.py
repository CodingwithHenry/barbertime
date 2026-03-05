import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import get_current_shop
from app.core.upload import validate_image_bytes, delete_upload, UPLOAD_DIR, MAX_UPLOAD_BYTES
from app.models.shop import Shop
from app.models.employee import Employee
from app.schemas.shop import ShopPrivate, ShopProfileUpdate, ShopStatusUpdate
from app.services.queue_suggestion import record_wait_time
from app.services.websocket_manager import manager

router = APIRouter(prefix="/shops", tags=["shops"])


@router.get("/me", response_model=ShopPrivate)
async def get_me(shop: Shop = Depends(get_current_shop)):
    return shop


@router.patch("/me", response_model=ShopPrivate)
async def update_profile(
    body: ShopProfileUpdate,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(shop, field, value)
    await db.commit()
    await db.refresh(shop)
    return shop


@router.post("/me/photo", response_model=ShopPrivate)
async def upload_photo(
    file: UploadFile = File(...),
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 5 MB)")
    validate_image_bytes(data)
    filename = f"{uuid.uuid4().hex}"  # no user-supplied extension; browser sniffs correctly
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, filename)  # uuid hex only, no path traversal possible
    async with aiofiles.open(path, "wb") as f:
        await f.write(data)
    old_url = shop.photo_url
    shop.photo_url = f"/uploads/{filename}"
    await db.commit()
    await db.refresh(shop)
    delete_upload(old_url)
    return shop


@router.patch("/me/status", response_model=ShopPrivate)
async def update_status(
    body: ShopStatusUpdate,
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    old_wait = shop.wait_time
    shop.status = body.status
    shop.wait_time = body.wait_time
    await db.commit()
    await db.refresh(shop)

    # Record history if wait time changed
    if body.wait_time != old_wait:
        await record_wait_time(db, shop.id, body.wait_time)

    # Broadcast real-time update
    await manager.broadcast(shop.id, {
        "type": "status_update",
        "status": shop.status,
        "wait_time": shop.wait_time,
    })
    return shop


@router.get("/me/suggest-wait-time")
async def get_wait_suggestion(
    shop: Shop = Depends(get_current_shop),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.avg(Employee.wait_time))
        .where(Employee.shop_id == shop.id, Employee.is_active == True, Employee.wait_time > 0)
    )
    avg = result.scalar_one_or_none()
    suggested = int(round(avg)) if avg is not None else 15
    return {"suggested_wait_time": suggested}
