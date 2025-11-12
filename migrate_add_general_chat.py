"""
Database Migration: Add general_chat_messages table

This script creates the new general_chat_messages table to persist
general chat history across server restarts.

Author: Socializer Development Team
Date: 2024-11-12
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datamanager.data_model import DataModel, Base
from sqlalchemy import inspect


def run_migration():
    """Create the general_chat_messages table if it doesn't exist."""
    
    print("\n" + "="*60)
    print("DATABASE MIGRATION: Add general_chat_messages table")
    print("="*60 + "\n")
    
    try:
        # Initialize database
        data_model = DataModel()
        engine = data_model.engine
        
        # Check if table already exists
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"📊 Found {len(existing_tables)} existing tables:")
        for table in sorted(existing_tables):
            print(f"   • {table}")
        
        if 'general_chat_messages' in existing_tables:
            print("\n✅ Table 'general_chat_messages' already exists - skipping creation")
        else:
            print("\n📝 Creating table 'general_chat_messages'...")
            
            # Create all tables (will only create missing ones)
            Base.metadata.create_all(bind=engine)
            
            # Verify creation
            inspector = inspect(engine)
            if 'general_chat_messages' in inspector.get_table_names():
                print("✅ Table 'general_chat_messages' created successfully!")
                
                # Show table structure
                columns = inspector.get_columns('general_chat_messages')
                print("\n📋 Table structure:")
                for col in columns:
                    print(f"   • {col['name']}: {col['type']}")
            else:
                print("❌ Failed to create table 'general_chat_messages'")
                return False
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETE")
        print("="*60)
        print("""
General chat messages will now persist across server restarts!

Benefits:
✅ Chat history survives server restarts
✅ Users see recent messages when joining
✅ Database-backed persistence
✅ Automatic cleanup of old messages
""")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
