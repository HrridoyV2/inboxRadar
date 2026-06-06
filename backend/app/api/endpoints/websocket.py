from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging
from app.db.models import EmailModel
from app.services import email_poller

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        # We make a copy of the connection list in case it changes during iteration
        connections = list(self.active_connections)
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Error broadcasting to connection, removing: {e}")
                self.disconnect(connection)

    async def broadcast_new_email(self, email_model: EmailModel):
        message = {
            "type": "NEW_EMAIL",
            "email": {
                "id": str(email_model.id),
                "message_id": email_model.message_id,
                "sender": email_model.sender,
                "subject": email_model.subject,
                "body": email_model.body,
                "received_at": email_model.received_at.isoformat() if email_model.received_at else None,
                "is_important": email_model.is_important,
                "priority": email_model.priority,
                "category": email_model.category,
                "reason": email_model.reason,
                "created_at": email_model.created_at.isoformat() if email_model.created_at else None
            }
        }
        await self.broadcast(message)


# Initialize global manager and bind it to the poller
manager = ConnectionManager()
email_poller.websocket_manager = manager

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep connection open and listen for client heartbeats/messages
        while True:
            data = await websocket.receive_text()
            # Simple heartbeat response
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
