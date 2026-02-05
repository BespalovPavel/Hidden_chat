import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.application.manager import manager
from backend.application.schemas import Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws")

@router.websocket("/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str, username: str):
    await manager.connect(websocket, room_id, user_id)
    
    await manager.broadcast_message(room_id, Message(
        type="system",
        text=f"{username} присоединился к чату"
    ))
    
    try:
        while True:
            data = await websocket.receive_json()
            
            message_payload = Message(
                type = "message",
                user_id = user_id,
                username = username,
                text = data.get("message", ""),
            )
            
            await manager.broadcast_message(room_id, message_payload)
            
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        await manager.broadcast_message(room_id, Message(
            type = "system",
            text = f"{username} покинул чат"
        ))
    except Exception as e:
        logger.error(f"Error: {e}")
        manager.disconnect(room_id, user_id)