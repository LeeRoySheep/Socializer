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

# ==================== LLM Configuration Schemas ====================

class LLMConfigBase(BaseModel):
    """Base schema for LLM configuration."""
    provider: Optional[str] = Field(
        None, 
        description="LLM provider (e.g., 'lm_studio', 'ollama', 'openai', 'gemini', 'claude')",
        example="lm_studio"
    )
    endpoint: Optional[str] = Field(
        None,
        description="Custom endpoint URL with IP and port (e.g., 'http://192.168.1.100:1234')",
        example="http://192.168.1.100:1234"
    )
    model: Optional[str] = Field(
        None,
        description="Model name (e.g., 'llama-3.2', 'local-model', 'gpt-4o-mini')",
        example="llama-3.2"
    )

class LLMConfigCreate(LLMConfigBase):
    """Schema for creating/updating LLM configuration."""
    
    @validator('endpoint')
    def validate_endpoint(cls, v):
        """Validate endpoint URL format if provided."""
        if v is not None:
            # Basic URL validation - must start with http:// or https://
            if not v.startswith(('http://', 'https://')):
                raise ValueError('Endpoint must start with http:// or https://')
            # Check for port number - must be in format http://host:port or http://host:port/path
            # Split by '/' to get the host:port part (after http://)
            parts = v.split('/')
            if len(parts) >= 3:  # ['http:', '', 'host:port', ...]
                host_port = parts[2]
                if ':' not in host_port:
                    raise ValueError('Endpoint must include a port number (e.g., http://192.168.1.100:1234)')
            else:
                raise ValueError('Invalid endpoint URL format')
        return v
    
    @validator('provider')
    def validate_provider(cls, v):
        """Validate provider is one of the supported options."""
        if v is not None:
            valid_providers = ['lm_studio', 'ollama', 'openai', 'gemini', 'claude']
            if v not in valid_providers:
                raise ValueError(f'Provider must be one of: {", ".join(valid_providers)}')
        return v

class LLMConfigResponse(LLMConfigBase):
    """Schema for LLM configuration response."""
    user_id: int
    
    class Config:
        orm_mode = True
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "provider": "lm_studio",
                "endpoint": "http://192.168.1.100:1234",
                "model": "llama-3.2"
            }
        }
