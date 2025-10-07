"""Chat-related routes for the application."""
import json
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..dependencies import get_current_user
from ..database import get_db
from ..websocket.connection_manager import ConnectionManager

router = APIRouter()

# Initialize WebSocket connection manager
manager = ConnectionManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: Optional[str] = None):
    """WebSocket endpoint for real-time chat."""
    # Authenticate the user from the token
    try:
        # In a real application, you would validate the JWT token here
        # For this example, we'll just use the client_id as the username
        username = client_id
        
        # Accept the WebSocket connection
        await manager.connect(websocket, username)
        
        try:
            while True:
                # Receive message from WebSocket
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle different message types
                if message_data.get("type") == "chat":
                    # Broadcast the message to all connected clients
                    await manager.broadcast({
                        "type": "chat",
                        "from": username,
                        "message": message_data["message"],
                        "timestamp": str(datetime.utcnow())
                    })
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, username)
            await manager.broadcast({
                "type": "status",
                "message": f"{username} left the chat",
                "timestamp": str(datetime.utcnow())
            })
            
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await websocket.close()

@router.get("/messages", response_model=List[schemas.MessageResponse])
async def get_messages(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a list of chat messages."""
    messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).offset(skip).limit(limit).all()
    return messages

@router.post("/send", response_model=schemas.MessageResponse)
async def send_message(
    message: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Send a new chat message."""
    db_message = models.Message(
        sender_id=current_user.id,
        content=message.content,
        timestamp=datetime.utcnow()
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    # Broadcast the message to all connected clients
    await manager.broadcast({
        "type": "chat",
        "from": current_user.username,
        "message": message.content,
        "timestamp": str(db_message.timestamp)
    })
    
    return db_message
