"""
WebSocket connection manager for handling multiple WebSocket connections.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

# Configure logging
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and handles broadcasting messages."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[str, List[WebSocket]] = {}
        self.connection_info: Dict[str, Dict[str, Any]] = {}  # Additional connection metadata
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[str] = None, username: Optional[str] = None):
        """Accept a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to accept
            client_id: A unique identifier for the client
            user_id: Optional user ID if the user is authenticated
            username: Optional username if the user is authenticated
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # Accept the WebSocket connection
            await websocket.accept()
            
            # Store the connection
            async with self._lock:
                self.active_connections[client_id] = websocket
                self.connection_info[client_id] = {
                    'user_id': user_id,
                    'username': username,  # Store username to avoid repeated DB queries
                    'connected_at': asyncio.get_event_loop().time(),
                    'last_active': asyncio.get_event_loop().time(),
                    'state': WebSocketState.CONNECTED
                }
                
                if user_id:
                    if user_id not in self.user_connections:
                        self.user_connections[user_id] = []
                    self.user_connections[user_id].append(websocket)
            
            logger.info(f"New WebSocket connection: {client_id} (User: {username or user_id or 'unauthenticated'})")
            return True
            
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}", exc_info=True)
            return False

    async def disconnect(self, client_id: str, user_id: Optional[str] = None):
        """Remove a WebSocket connection.
        
        Args:
            client_id: The ID of the client to disconnect
            user_id: Optional user ID if the user was authenticated
        """
        async with self._lock:
            # Remove from active connections
            if client_id in self.active_connections:
                try:
                    websocket = self.active_connections[client_id]
                    if websocket.client_state != WebSocketState.DISCONNECTED:
                        await websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing WebSocket connection {client_id}: {e}")
                finally:
                    del self.active_connections[client_id]
            
            # Remove from user connections
            if user_id and user_id in self.user_connections:
                user_connections = self.user_connections[user_id]
                user_connections = [conn for conn in user_connections 
                                  if conn != self.active_connections.get(client_id)]
                
                if not user_connections:
                    del self.user_connections[user_id]
                else:
                    self.user_connections[user_id] = user_connections
            
            # Remove connection info
            if client_id in self.connection_info:
                del self.connection_info[client_id]
            
            logger.info(f"Disconnected WebSocket: {client_id} (User: {user_id or 'unknown'})")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection.
        
        Args:
            message: The message to send
            websocket: The WebSocket connection to send the message to
            
        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(message)
                self._update_connection_activity(websocket)
                return True
            return False
        except (WebSocketDisconnect, RuntimeError) as e:
            logger.warning(f"Failed to send message to WebSocket: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}", exc_info=True)
            return False

    async def broadcast(self, message: str, skip_connections: Optional[Set[WebSocket]] = None):
        """Send a message to all active WebSocket connections.
        
        Args:
            message: The message to broadcast
            skip_connections: Optional set of connections to skip
        """
        skip_connections = skip_connections or set()
        tasks = []
        
        async with self._lock:
            connections = list(self.active_connections.values())
        
        for connection in connections:
            if connection in skip_connections:
                continue
                
            if connection.client_state == WebSocketState.CONNECTED:
                tasks.append(self.send_personal_message(message, connection))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def send_to_user(self, user_id: str, message: str, skip_connection: Optional[WebSocket] = None):
        """Send a message to all connections of a specific user.
        
        Args:
            user_id: The ID of the user to send the message to
            message: The message to send
            skip_connection: Optional specific connection to skip
        """
        if not user_id or user_id not in self.user_connections:
            return
            
        tasks = []
        
        async with self._lock:
            connections = list(self.user_connections.get(user_id, []))
        
        for connection in connections:
            if connection == skip_connection:
                continue
                
            if connection.client_state == WebSocketState.CONNECTED:
                tasks.append(self.send_personal_message(message, connection))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _update_connection_activity(self, websocket: WebSocket):
        """Update the last activity timestamp for a connection."""
        for client_id, conn in self.active_connections.items():
            if conn == websocket and client_id in self.connection_info:
                self.connection_info[client_id]['last_active'] = asyncio.get_event_loop().time()
                break
    
    def get_user_connections(self, user_id: str) -> List[WebSocket]:
        """Get all active connections for a user."""
        return [conn for conn in self.user_connections.get(user_id, []) 
                if conn.client_state == WebSocketState.CONNECTED]
    
    def get_connection_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection."""
        return self.connection_info.get(client_id)

# Create a global instance of the connection manager
manager = ConnectionManager()
