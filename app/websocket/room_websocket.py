"""
WebSocket handler for private chat rooms.

Provides real-time messaging for private rooms with multiple users and AI.
"""

import json
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect, status
from datetime import datetime

from datamanager.data_manager import DataManager
from datamanager.data_model import User

logger = logging.getLogger(__name__)


class RoomConnectionManager:
    """
    Manages WebSocket connections for private chat rooms.
    
    Handles:
    - User connections to specific rooms
    - Broadcasting messages to room members
    - Real-time invite notifications
    - Online presence for room members
    """
    
    def __init__(self):
        """Initialize the room connection manager."""
        # room_id -> set of websocket connections
        self.room_connections: Dict[int, Set[WebSocket]] = {}
        # websocket -> user_id
        self.connection_users: Dict[WebSocket, int] = {}
        # user_id -> set of websockets (user can have multiple tabs)
        self.user_sockets: Dict[int, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        """
        Connect a user to a room.
        
        Args:
            websocket: WebSocket connection
            room_id: ID of the room to join
            user_id: ID of the user connecting
        """
        await websocket.accept()
        
        # Add to room connections
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(websocket)
        
        # Track user
        self.connection_users[websocket] = user_id
        if user_id not in self.user_sockets:
            self.user_sockets[user_id] = set()
        self.user_sockets[user_id].add(websocket)
        
        logger.info(f"User {user_id} connected to room {room_id}")
        
        # Notify room members that user joined
        await self.broadcast_to_room(room_id, {
            "type": "user_joined",
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": datetime.utcnow().isoformat()
        }, exclude=websocket)
    
    async def disconnect(self, websocket: WebSocket, room_id: int):
        """
        Disconnect a user from a room.
        
        Args:
            websocket: WebSocket connection
            room_id: ID of the room to leave
        """
        user_id = self.connection_users.get(websocket)
        
        # Remove from room
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(websocket)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
        
        # Remove from user tracking
        if websocket in self.connection_users:
            del self.connection_users[websocket]
        
        if user_id and user_id in self.user_sockets:
            self.user_sockets[user_id].discard(websocket)
            if not self.user_sockets[user_id]:
                del self.user_sockets[user_id]
        
        if user_id:
            logger.info(f"User {user_id} disconnected from room {room_id}")
            
            # Notify room members that user left
            await self.broadcast_to_room(room_id, {
                "type": "user_left",
                "user_id": user_id,
                "room_id": room_id,
                "timestamp": datetime.utcnow().isoformat()
            })
    
    async def broadcast_to_room(
        self, 
        room_id: int, 
        message: dict,
        exclude: Optional[WebSocket] = None
    ):
        """
        Broadcast a message to all members of a room.
        
        Args:
            room_id: ID of the room
            message: Message dictionary to send
            exclude: Optional websocket to exclude from broadcast
        """
        if room_id not in self.room_connections:
            return
        
        disconnected = set()
        
        for connection in self.room_connections[room_id]:
            if connection == exclude:
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection, room_id)
    
    async def send_to_user(self, user_id: int, message: dict):
        """
        Send a message to a specific user (all their connections).
        
        Args:
            user_id: ID of the user
            message: Message dictionary to send
        """
        if user_id not in self.user_sockets:
            return
        
        disconnected = set()
        
        for connection in self.user_sockets[user_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            if connection in self.connection_users:
                user_id = self.connection_users[connection]
                # Find room_id for this connection (we need to track this better)
                # For now, remove from user_sockets
                self.user_sockets[user_id].discard(connection)
                if not self.user_sockets[user_id]:
                    del self.user_sockets[user_id]
                del self.connection_users[connection]
    
    def is_user_online(self, user_id: int) -> bool:
        """
        Check if a user is currently online.
        
        Args:
            user_id: ID of the user
            
        Returns:
            bool: True if user has active connections
        """
        return user_id in self.user_sockets and len(self.user_sockets[user_id]) > 0
    
    def get_room_online_users(self, room_id: int) -> Set[int]:
        """
        Get all online users in a room.
        
        Args:
            room_id: ID of the room
            
        Returns:
            Set of user IDs currently connected to the room
        """
        if room_id not in self.room_connections:
            return set()
        
        online_users = set()
        for connection in self.room_connections[room_id]:
            if connection in self.connection_users:
                online_users.add(self.connection_users[connection])
        
        return online_users


# Global room connection manager instance
room_manager = RoomConnectionManager()


def get_dm() -> DataManager:
    """Get DataManager instance."""
    return DataManager("data.sqlite.db")


async def handle_room_websocket(
    websocket: WebSocket,
    room_id: int,
    current_user: User
):
    """
    WebSocket endpoint for room messaging.
    
    Handles:
    - Real-time message delivery
    - User presence
    - Typing indicators
    - Message acknowledgments
    
    Message format:
    {
        "type": "message" | "typing" | "read",
        "content": "message text",
        "room_id": 123
    }
    
    Args:
        websocket: WebSocket connection
        room_id: ID of the room
        current_user: Authenticated user
    """
    dm = get_dm()
    
    # Verify user has access to room
    if not dm.is_user_in_room(current_user.id, room_id):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Connect user to room
    await room_manager.connect(websocket, room_id, current_user.id)
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "room_id": room_id,
            "user_id": current_user.id,
            "message": "Connected to room"
        })
        
        # Main message loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "message")
            
            if message_type == "message":
                # User sent a message
                content = message_data.get("content", "")
                
                if content.strip():
                    # Save message to database
                    saved_message = dm.add_room_message(
                        room_id=room_id,
                        sender_id=current_user.id,
                        content=content,
                        sender_type="user",
                        message_type="text"
                    )
                    
                    if saved_message:
                        # Broadcast to all room members
                        await room_manager.broadcast_to_room(room_id, {
                            "type": "message",
                            "message_id": saved_message.id,
                            "room_id": room_id,
                            "sender_id": current_user.id,
                            "sender_username": current_user.username,
                            "sender_type": "user",
                            "content": content,
                            "timestamp": saved_message.created_at.isoformat()
                        })
                        
                        # Trigger AI response if ai_enabled
                        room = dm.get_room(room_id)
                        if room and room.ai_enabled:
                            # Import AI service
                            from app.services.room_ai_service import get_room_ai_service
                            ai_service = get_room_ai_service()
                            
                            # Get recent messages for context
                            recent_messages = dm.get_room_messages(room_id, limit=20)
                            
                            # Check if AI should respond
                            should_respond = await ai_service.should_ai_respond(
                                room, recent_messages, saved_message
                            )
                            
                            if should_respond:
                                # Generate AI response
                                ai_response = await ai_service.generate_room_response(
                                    room, current_user, content, recent_messages
                                )
                                
                                if ai_response:
                                    # Save AI message
                                    ai_message = dm.add_room_message(
                                        room_id=room_id,
                                        sender_id=None,  # AI has no sender_id
                                        content=ai_response,
                                        sender_type="ai",
                                        message_type="text"
                                    )
                                    
                                    if ai_message:
                                        # Broadcast AI response
                                        await room_manager.broadcast_to_room(room_id, {
                                            "type": "message",
                                            "message_id": ai_message.id,
                                            "room_id": room_id,
                                            "sender_id": None,
                                            "sender_username": "AI Assistant",
                                            "sender_type": "ai",
                                            "content": ai_response,
                                            "timestamp": ai_message.created_at.isoformat()
                                        })
            
            elif message_type == "typing":
                # User is typing
                await room_manager.broadcast_to_room(room_id, {
                    "type": "typing",
                    "user_id": current_user.id,
                    "username": current_user.username,
                    "room_id": room_id
                }, exclude=websocket)
            
            elif message_type == "read":
                # User read messages
                message_id = message_data.get("message_id")
                # TODO: Update last_read_at for user in room_members
                pass
    
    except WebSocketDisconnect:
        logger.info(f"User {current_user.id} disconnected from room {room_id}")
    except Exception as e:
        logger.error(f"Error in room websocket for user {current_user.id}: {e}")
    finally:
        await room_manager.disconnect(websocket, room_id)
