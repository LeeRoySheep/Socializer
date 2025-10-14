"""
Database Migration: Add Private Chat Room Tables

This script creates the new tables for private chat functionality:
- chat_rooms
- room_members  
- room_messages
- room_invites

Run this ONCE to add the tables to your database.
"""

from datamanager.data_model import Base, DataModel

def run_migration():
    """Create the new chat room tables."""
    print("🔄 Starting database migration...")
    print("   Adding private chat room tables...")
    
    # Initialize database
    db_model = DataModel("data.sqlite.db")
    
    # Create all tables (will only create new ones)
    Base.metadata.create_all(bind=db_model.engine)
    
    print("✅ Migration complete!")
    print("\nNew tables created:")
    print("  - chat_rooms")
    print("  - room_members")
    print("  - room_messages")
    print("  - room_invites")
    print("\n✅ Database is ready for private chat feature!")

if __name__ == "__main__":
    run_migration()
