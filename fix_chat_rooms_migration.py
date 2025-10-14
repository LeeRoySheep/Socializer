"""
Fix Chat Rooms Migration

Drop old chat_rooms table and recreate with new schema.
"""

import sqlite3
from datamanager.data_model import Base, DataModel

def fix_migration():
    """Drop old tables and recreate with new schema."""
    
    print("🔧 Fixing chat rooms migration...")
    
    # Connect to database
    conn = sqlite3.connect("data.sqlite.db")
    cursor = conn.cursor()
    
    # Drop old tables if they exist
    print("   Dropping old chat_rooms table...")
    cursor.execute("DROP TABLE IF EXISTS chat_rooms")
    cursor.execute("DROP TABLE IF EXISTS room_members")
    cursor.execute("DROP TABLE IF EXISTS room_messages")
    cursor.execute("DROP TABLE IF EXISTS room_invites")
    conn.commit()
    conn.close()
    
    print("   ✅ Old tables dropped")
    
    # Create new tables with correct schema
    print("   Creating new tables...")
    db_model = DataModel("data.sqlite.db")
    Base.metadata.create_all(bind=db_model.engine)
    
    print("✅ Migration fixed!")
    print("\nNew tables created with correct schema:")
    print("  - chat_rooms (with creator_id)")
    print("  - room_members")
    print("  - room_messages")
    print("  - room_invites")

if __name__ == "__main__":
    fix_migration()
