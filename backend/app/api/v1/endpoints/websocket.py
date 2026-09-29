"""
WebSocket endpoint for real-time command center updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.websocket_manager import ws_manager
from app.core.security import decode_access_token

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket connection authenticated via JWT token in query param.
    Client connects: ws://host/api/ws?token=<access_token>
    """
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = int(payload.get("sub", 0))
    if not user_id:
        await websocket.close(code=4001, reason="Invalid user")
        return

    await ws_manager.connect(websocket, user_id)
    try:
        # Send connection confirmation
        import json
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "data": {
                "user_id": user_id,
                "message": "Real-time connection established",
            }
        }))

        while True:
            # Keep connection alive — ping/pong
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
