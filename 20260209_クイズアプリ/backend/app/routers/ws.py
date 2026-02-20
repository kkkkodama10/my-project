"""WebSocket ルーター。"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import ws_manager

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    event_id = websocket.query_params.get("event_id")
    sid = websocket.cookies.get("session_id")

    if not event_id:
        await websocket.close(code=1008)
        return

    await ws_manager.connect(event_id, sid or "", websocket)

    try:
        while True:
            msg = await websocket.receive_text()
            await websocket.send_text(f"echo: {msg}")
    except WebSocketDisconnect:
        ws_manager.disconnect(event_id, sid or "")
    except Exception:
        ws_manager.disconnect(event_id, sid or "")
