"""Routers package for the application."""
from fastapi import APIRouter

# Import all routers
from . import auth, users, chat

# Create main router
api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
