"""SQLAlchemy models for the application."""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from ..database import Base

class User(Base):
    """User model for storing user information."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean(), default=True)
    is_admin = Column(Boolean(), default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="sender")
    chat_rooms = relationship("ChatRoom", back_populates="owner")
    memberships = relationship("RoomMembership", back_populates="user")

class Message(Base):
    """Message model for storing chat messages."""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=True)
    
    # Relationships
    sender = relationship("User", back_populates="messages")
    room = relationship("ChatRoom", back_populates="messages")

class ChatRoom(Base):
    """Chat room model for grouping messages."""
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    owner = relationship("User", back_populates="chat_rooms")
    messages = relationship("Message", back_populates="room")
    members = relationship("RoomMembership", back_populates="room")

class RoomMembership(Base):
    """Model for tracking user memberships in chat rooms."""
    __tablename__ = "room_memberships"

    id = Column(Integer, primary_key=True, index=True)
    is_admin = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("chat_rooms.id"), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="memberships")
    room = relationship("ChatRoom", back_populates="members")
