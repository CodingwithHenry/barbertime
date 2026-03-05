from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.shop import Shop
from sqlalchemy import select

from app.services.websocket_manager import manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/shops/{shop_id}")
async def shop_websocket(shop_id: int, ws: WebSocket):
    """Clients connect here to receive real-time status updates for a shop."""
    origin = ws.headers.get("origin", "")
    if origin and origin != settings.FRONTEND_URL:
        await ws.close(code=4003)
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Shop).where(Shop.id == shop_id, Shop.is_active == True))
        shop = result.scalar_one_or_none()
        if shop is None:
            await ws.close(code=4004)
            return

        await manager.connect(shop_id, ws)
        # Send current state immediately on connect
        await ws.send_json({
            "type": "initial",
            "status": shop.status,
            "wait_time": shop.wait_time,
        })

    try:
        while True:
            # Keep connection alive; we only push from server
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(shop_id, ws)
