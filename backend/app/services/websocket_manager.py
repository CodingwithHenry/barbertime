from fastapi import WebSocket
from typing import Dict, List


class ConnectionManager:
    def __init__(self):
        # shop_id -> list of websockets
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, shop_id: int, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(shop_id, []).append(ws)

    def disconnect(self, shop_id: int, ws: WebSocket):
        conns = self._connections.get(shop_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, shop_id: int, data: dict):
        conns = self._connections.get(shop_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(shop_id, ws)


manager = ConnectionManager()
