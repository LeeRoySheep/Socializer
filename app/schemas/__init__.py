"""Pydantic schemas for the application."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str

class TokenData(BaseModel):
    """Schema for JWT token data."""
    username: Optional[str] = None

class UserBase(BaseModel):
    """Base schema for user data."""
    username: str
    email: EmailStr
    is_active: bool = True
    is_admin: bool = False

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str

    @validator('password')
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserUpdate(UserBase):
    """Schema for updating user data."""
    password: Optional[str] = None
    email: Optional[EmailStr] = None

class UserInDB(UserBase):
    """Schema for user data in the database."""
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    """Schema for user response data."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    """Base schema for chat messages."""
    content: str = Field(..., min_length=1, max_length=1000)

class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    pass

class MessageResponse(MessageBase):
    """Schema for message response data."""
    id: int
    sender_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class ChatRoomBase(BaseModel):
    """Base schema for chat rooms."""
    name: str
    description: Optional[str] = None
    is_public: bool = True

class ChatRoomCreate(ChatRoomBase):
    """Schema for creating a new chat room."""
    pass

class ChatRoomResponse(ChatRoomBase):
    """Schema for chat room response data."""
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int

    class Config:
        orm_mode = True

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""
    type: str
    from_user: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
