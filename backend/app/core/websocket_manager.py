"""
WebSocket connection manager for real-time updates.
Broadcasts events to connected clients filtered by role/user.
"""
from typing import Optional
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        # {user_id: [WebSocket, ...]}
        self._connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = []
        self._connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self._connections:
            self._connections[user_id] = [
                ws for ws in self._connections[user_id] if ws != websocket
            ]
            if not self._connections[user_id]:
                del self._connections[user_id]

    async def send_to_user(self, user_id: int, event: dict):
        """Send an event to a specific user."""
        if user_id in self._connections:
            dead = []
            for ws in self._connections[user_id]:
                try:
                    await ws.send_text(json.dumps(event))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, user_id)

    async def broadcast(self, event: dict, exclude_user: Optional[int] = None):
        """Broadcast an event to all connected users."""
        for uid, connections in list(self._connections.items()):
            if uid == exclude_user:
                continue
            dead = []
            for ws in connections:
                try:
                    await ws.send_text(json.dumps(event))
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.disconnect(ws, uid)

    @property
    def active_connections(self) -> int:
        return sum(len(v) for v in self._connections.values())


# Global manager instance
ws_manager = ConnectionManager()


async def emit_event(event_type: str, data: dict, user_id: Optional[int] = None):
    """
    Emit a real-time event.
    If user_id is provided, sends only to that user.
    Otherwise broadcasts to all connected clients.
    """
    event = {
        "type": event_type,
        "data": data,
    }
    if user_id:
        await ws_manager.send_to_user(user_id, event)
    else:
        await ws_manager.broadcast(event)
