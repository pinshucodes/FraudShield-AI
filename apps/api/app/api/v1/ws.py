from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket import manager
from app.core.logging import get_logger

logger = get_logger("app.api.ws")

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just keep the connection open and wait for incoming messages if any,
            # though in this case we mainly want to broadcast from server to client.
            # Client might send ping messages to keep alive.
            data = await websocket.receive_text()
            if data == "ping":
                await manager.send_personal_message({"type": "PONG"}, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
