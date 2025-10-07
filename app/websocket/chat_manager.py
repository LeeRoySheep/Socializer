"""WebSocket connection and message manager for multi-user chat."""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from fastapi import WebSocket, status

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the connection manager."""
        if not self._initialized:
            # Active WebSocket connections mapped by client_id
            self.active_connections: Dict[str, WebSocket] = {}
            # User connections mapped by user_id to set of client_ids
            self.user_connections: Dict[str, Set[str]] = {}
            # User information mapped by user_id
            self.user_info: Dict[str, Dict] = {}
            # Mapping from client_id to user_id
            self.client_to_user: Dict[str, str] = {}
            # Room connections mapped by room_id to set of client_ids
            self.room_connections: Dict[str, Set[str]] = {}
            # Rooms mapped by room_id to set of user_ids
            self.rooms: Dict[str, Set[str]] = {}
            
            self.logger = logging.getLogger(__name__)
            self._initialized = True
            self.logger.info("ConnectionManager initialized")

    async def connect(self, websocket: WebSocket, client_id: str, user_id: str, username: str) -> None:
        """Register a new WebSocket connection.
        
        Args:
            websocket: The WebSocket connection (should already be accepted)
            client_id: Unique client identifier
            user_id: Authenticated user ID
            username: User's username
        """
        self.logger.info(f"Connecting client {client_id} for user {user_id} ({username})")
        
        # Store the connection
        self.active_connections[client_id] = websocket
        self.client_to_user[client_id] = user_id
        
        # Initialize user info if not exists
        if user_id not in self.user_info:
            self.user_info[user_id] = {
                'username': username,
                'status': 'online',
                'client_ids': set(),
                'last_seen': datetime.utcnow().isoformat()
            }
        
        # Update user info
        self.user_info[user_id]['status'] = 'online'
        self.user_info[user_id]['client_ids'].add(client_id)
        self.user_info[user_id]['last_seen'] = datetime.utcnow().isoformat()
        
        # Track user's connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(client_id)
        
        self.logger.info(f"User {username} ({user_id}) connected with client {client_id}")
    
    async def disconnect(self, client_id: str, user_id: str = None) -> None:
        """Remove a WebSocket connection and update user status.
        
        Args:
            client_id: The client ID to disconnect
            user_id: Optional user ID (will be looked up if not provided)
        """
        # Check if already disconnected
        if client_id not in self.active_connections and client_id not in self.client_to_user:
            self.logger.debug(f"Client {client_id} already disconnected")
            return
        
        if not user_id:
            user_id = self.client_to_user.get(client_id)
            if not user_id:
                self.logger.warning(f"No user found for client {client_id}")
                return
        
        # Remove from active connections
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        # Remove from client_to_user mapping
        if client_id in self.client_to_user:
            del self.client_to_user[client_id]
        
        # Update user connections
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(client_id)
            
            # If this was the last connection for this user, mark as offline
            if not self.user_connections[user_id]:
                if user_id in self.user_info:
                    self.user_info[user_id]['status'] = 'offline'
                    self.user_info[user_id]['last_seen'] = datetime.utcnow().isoformat()
                    self.logger.info(f"User {user_id} is now offline (no active connections)")
        
        # Clean up user info if no more connections
        if user_id in self.user_info:
            self.user_info[user_id]['client_ids'].discard(client_id)
        
        # Remove from all rooms
        for room_id in list(self.room_connections.keys()):
            if client_id in self.room_connections[room_id]:
                self.room_connections[room_id].discard(client_id)
                # Clean up empty room
                if not self.room_connections[room_id]:
                    del self.room_connections[room_id]
        
        # Remove user from rooms if they have no more connections
        if user_id in self.user_connections and not self.user_connections[user_id]:
            for room_id in list(self.rooms.keys()):
                if user_id in self.rooms[room_id]:
                    self.rooms[room_id].discard(user_id)
                    # Clean up empty room
                    if not self.rooms[room_id]:
                        del self.rooms[room_id]
            
        self.logger.info(f"Client {client_id} disconnected from user {user_id}")
    
    async def broadcast_user_status(self, user_id: str, status: str) -> None:
        """Broadcast a user's status change to all connected clients.
        
        Args:
            user_id: The user ID whose status changed
            status: The new status (e.g., 'online', 'offline', 'away')
        """
        if user_id not in self.user_info:
            return
            
        user_info = self.user_info[user_id]
        username = user_info.get('username', 'unknown')
        
        message = {
            'type': 'user_status',
            'user_id': user_id,
            'username': username,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Send to all active connections
        for client_id, websocket in list(self.active_connections.items()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                self.logger.error(f"Error broadcasting to client {client_id}: {e}")
    
    async def is_user_online(self, user_id: str) -> bool:
        """Check if a user is currently online.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            bool: True if the user is online, False otherwise
        """
        if user_id not in self.user_info:
            return False
        return self.user_info[user_id].get('status') == 'online' and bool(self.user_connections.get(user_id))

    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client.
        
        Args:
            message: The message to send (will be JSON-encoded)
            client_id: The target client ID
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")

    def get_online_users(self, room_id: str = None) -> List[Dict[str, Any]]:
        """Get a list of online users.
        
        Args:
            room_id: If provided, only return users in this room
            
        Returns:
            List of user dictionaries with id, username, and status
        """
        users = []
        for user_id, conns in self.user_connections.items():
            if user_id in self.user_info and conns:  # Only include users with active connections
                user_data = self.user_info[user_id].copy()
                user_data['id'] = user_id
                if room_id:
                    # Only include users in the specified room
                    user_conns = self.user_connections[user_id]
                    if any(conn_id in self.room_connections.get(room_id, set()) for conn_id in user_conns):
                        users.append(user_data)
                else:
                    users.append(user_data)
        return users
        
    async def broadcast_online_users(self, room_id: str = None, exclude: List[str] = None):
        """Broadcast the updated online users list to all clients in a room.
        
        Args:
            room_id: The room to broadcast to (None for all rooms)
            exclude: List of client IDs to exclude
        """
        if exclude is None:
            exclude = []
            
        online_users = self.get_online_users(room_id)
        message = {
            "type": "online_users",
            "users": online_users,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast(message, room_id, exclude)
        
    async def broadcast(self, message: dict, room_id: str = None, exclude: List[str] = None):
        """Broadcast a message to all active connections in a room or globally.
        
        Args:
            message: The message to broadcast (will be JSON-encoded)
            room_id: If provided, only send to clients in this room
            exclude: List of client IDs to exclude from the broadcast
        """
        if exclude is None:
            exclude = []
            
        if room_id and room_id in self.room_connections:
            # Send to all clients in the specified room
            for client_id in self.room_connections[room_id]:
                if client_id not in exclude and client_id in self.active_connections:
                    try:
                        await self.active_connections[client_id].send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {client_id}: {e}")
        else:
            # Send to all active connections
            for client_id, connection in self.active_connections.items():
                if client_id not in exclude:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.error(f"Error broadcasting to {client_id}: {e}")
        
    async def send_online_users(self, client_id: str, room_id: str = None):
        """Send the list of online users to a specific client.
        
        Args:
            client_id: The client ID to send the list to
            room_id: The room to get users from (None for all rooms) - currently ignored
        """
        if client_id not in self.active_connections:
            return
            
        online_users = self.get_online_users(room_id)
        message = {
            'type': 'online_users',
            'users': online_users,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        await self.send_personal_message(message, client_id)

    async def join_room(self, client_id: str, user_id: str, room_id: str):
        """Add a connection to a room.
        
        Args:
            client_id: The client ID to add to the room
            user_id: The user ID associated with the connection
            room_id: The room ID to join
        """
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        if room_id not in self.rooms:
            self.rooms[room_id] = set()
            
        self.room_connections[room_id].add(client_id)
        self.rooms[room_id].add(user_id)
        
        # Update user info
        if user_id in self.user_info:
            self.user_info[user_id]['status'] = 'online'
            self.user_info[user_id]['last_seen'] = None
        logger.info(f"User {user_id} (client {client_id}) joined room {room_id}")
        
        # Notify room about new user
        await self.broadcast({
            "type": "user_joined",
            "user_id": user_id,
            "room_id": room_id,
            "timestamp": self._get_timestamp()
        }, room_id)

    def leave_room(self, client_id: str, user_id: str, room_id: str):
        """Remove a client from a chat room.
        
        Args:
            client_id: The client ID to remove from the room
            user_id: The user ID associated with the client
            room_id: The room ID to leave
        """
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(client_id)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
            logger.info(f"User {user_id} (client {client_id}) left room {room_id}")

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat()

# Global instance of the connection manager
manager = ConnectionManager()
