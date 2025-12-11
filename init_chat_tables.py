#!/usr/bin/env python3
"""
Initialize Chat Tables in Database
===================================

PURPOSE:
    Create the chat-related tables (messages, chat_rooms, room_memberships) 
    that are missing from the database.

LOCATION:
    init_chat_tables.py (root directory)

ISSUE:
    The Message model is defined in app/models/__init__.py but the tables
    were never created in the database, causing:
    "sqlalchemy.exc.OperationalError: no such table: messages"

SOLUTION:
    Import all models and create tables using SQLAlchemy's create_all()

TRACEABILITY:
    - Models defined in: app/models/__init__.py
    - Database config: app/database.py
    - Related issue: Chat messages endpoint returns 404
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, Base, create_tables
from app.models import User, Message, ChatRoom, RoomMembership

def init_chat_tables():
    """
    Create all chat-related tables in the database.
    
    Tables created:
    - messages: Store chat messages
    - chat_rooms: Store chat room definitions
    - room_memberships: Track user memberships in rooms
    
    Note: This will NOT drop existing tables or data.
    It only creates missing tables.
    """
    print("="*80)
    print("INITIALIZING CHAT TABLES")
    print("="*80)
    
    # Import models to register them with Base
    print("\n✅ Models imported:")
    print(f"  - User: {User.__tablename__}")
    print(f"  - Message: {Message.__tablename__}")
    print(f"  - ChatRoom: {ChatRoom.__tablename__}")
    print(f"  - RoomMembership: {RoomMembership.__tablename__}")
    
    # Create all tables (this is safe - won't drop existing ones)
    print("\n🔨 Creating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    # Verify tables exist
    print("\n📋 Verifying tables...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    required_tables = ['users', 'messages', 'chat_rooms', 'room_memberships']
    
    for table in required_tables:
        if table in existing_tables:
            print(f"  ✅ {table} - EXISTS")
        else:
            print(f"  ❌ {table} - MISSING")
    
    print("\n" + "="*80)
    print("✅ INITIALIZATION COMPLETE")
    print("="*80)
    print("\n💡 You can now:")
    print("  - Access /chat/messages endpoint")
    print("  - Send messages via /chat/send")
    print("  - Use WebSocket connections")
    
    return True

if __name__ == "__main__":
    print("\n🚀 Starting database initialization...\n")
    success = init_chat_tables()
    
    if success:
        print("\n✅ Database ready for chat functionality!")
        sys.exit(0)
    else:
        print("\n❌ Database initialization failed!")
        sys.exit(1)
