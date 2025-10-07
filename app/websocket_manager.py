"""WebSocket connection manager for real-time communication."""
import json
from typing import Dict, Optional, List
from fastapi import WebSocket, status

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Store a new WebSocket connection.
        
        Note: The WebSocket connection should already be accepted before calling this method.
        """
        if client_id in self.active_connections:
            # Disconnect existing connection if it exists
            await self.active_connections[client_id].close()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str) -> None:
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_message(self, message: dict, client_id: str) -> bool:
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
            return True
        return False

    async def broadcast(self, message: dict, exclude: Optional[list] = None) -> None:
        """Broadcast a message to all connected clients, optionally excluding some."""
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
