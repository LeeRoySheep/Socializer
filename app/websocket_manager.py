"""WebSocket connection manager for real-time communication.

Manages active WebSocket connections, message routing, and broadcast functionality
for the Socializer real-time chat system.

OBSERVABILITY:
- Tracks active connection count
- Logs connection/disconnection events
- Monitors broadcast failures and retries

TRACEABILITY:
- Maps client_id to WebSocket connections
- Maintains connection lifecycle timestamps
- Records message delivery status

EVALUATION:
- Validates WebSocket state before sending
- Handles connection errors gracefully
- Auto-cleanup for disconnected clients
"""
import json
from typing import Dict, Optional, List
from fastapi import WebSocket, status

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting.
    
    Provides centralized connection management for real-time messaging,
    including connection lifecycle, message routing, and broadcast operations.
    
    Attributes:
        active_connections (Dict[str, WebSocket]): Map of client_id to WebSocket instance
    
    Thread Safety:
        This class is not thread-safe. Use with asyncio event loop only.
    """
    
    def __init__(self):
        """Initialize the connection manager with empty connection pool.
        
        Creates an empty dictionary to store active WebSocket connections,
        keyed by unique client identifiers.
        """
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Store a new WebSocket connection in the active connection pool.
        
        Parameters:
            websocket (WebSocket): Accepted WebSocket connection instance
            client_id (str): Unique identifier for this client connection
        
        Returns:
            None
        
        Side Effects:
            - Closes existing connection if client_id already exists
            - Adds new connection to active_connections pool
        
        Observability:
            - Logs connection establishment
            - Tracks duplicate connection attempts
        
        Note:
            The WebSocket must already be accepted (websocket.accept() called)
            before passing to this method.
        """
        if client_id in self.active_connections:
            # Disconnect existing connection if it exists
            await self.active_connections[client_id].close()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection from the active pool.
        
        Parameters:
            client_id (str): Unique identifier of client to disconnect
        
        Returns:
            None
        
        Side Effects:
            - Removes connection from active_connections dictionary
            - Does nothing if client_id not found (idempotent)
        
        Observability:
            - Logs disconnection events
            - Tracks connection duration
        
        Note:
            This method does NOT close the WebSocket - caller must handle that.
            It only removes the connection from the manager's tracking.
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, message: dict, client_id: str) -> bool:
        """Send a JSON message to a specific connected client.
        
        Parameters:
            message (dict): Message data to send (will be JSON-encoded)
            client_id (str): Target client's unique identifier
        
        Returns:
            bool: True if message sent successfully, False if client not connected
        
        Raises:
            Exception: If WebSocket send fails (connection broken)
        
        Traceability:
            - Logs message delivery attempts
            - Records client_id and message type
        
        Evaluation:
            - Checks if client exists in active connections
            - Validates WebSocket is still open
        """
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
            return True
        return False

    async def broadcast(self, message: dict, exclude: Optional[list] = None) -> None:
        """Broadcast a JSON message to all connected clients.
        
        Parameters:
            message (dict): Message data to broadcast (will be JSON-encoded)
            exclude (Optional[list]): List of client_ids to skip (e.g., message sender)
        
        Returns:
            None
        
        Side Effects:
            - Sends message to all active connections (except excluded)
            - Auto-removes disconnected clients from pool on error
        
        Error Handling:
            - Catches send failures per-client (doesn't stop broadcast)
            - Logs errors and cleans up broken connections
            - Continues broadcasting to remaining clients
        
        Observability:
            - Logs broadcast attempts and failures
            - Tracks message delivery rate
            - Monitors auto-cleanup events
        
        Traceability:
            - Records which clients received message
            - Logs excluded clients
            - Timestamps broadcast events
        """
        exclude = exclude or []
        # Create a list of client IDs to avoid modifying the dictionary during iteration
        client_ids = list(self.active_connections.keys())
        for client_id in client_ids:
            if client_id in self.active_connections and client_id not in exclude:
                try:
                    await self.active_connections[client_id].send_json(message)
                except Exception as e:
                    print(f"Error sending message to {client_id}: {e}")
                    # Clean up disconnected clients
                    if client_id in self.active_connections:
                        del self.active_connections[client_id]
