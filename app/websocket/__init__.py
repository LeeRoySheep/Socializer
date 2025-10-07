"""WebSocket package for real-time communication.

This package provides WebSocket endpoints and connection management for real-time
features like chat, notifications, and AI interactions.
"""
from fastapi import APIRouter

# Import WebSocket routes
from .routes import router as websocket_router

# Import connection manager
from .connection_manager import ConnectionManager, manager as connection_manager

# The main WebSocket router that includes all WebSocket routes
router = APIRouter()

# Include the WebSocket routes
router.include_router(websocket_router, tags=["WebSocket"])

# Export the router and connection manager
__all__ = ["router", "ConnectionManager", "connection_manager"]
