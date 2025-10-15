"""
Migration: Add Room Visibility Field
=====================================

Adds 'is_public' field to chat_rooms table to distinguish between:
- Public rooms (discoverable, can be found by others)
- Hidden rooms (invite-only, not discoverable)

This enables invite-only rooms that don't need passwords since they're
not discoverable by uninvited users.

Date: 2025-10-15
"""

import sqlite3
import sys


def run_migration():
    """
    Add is_public column to chat_rooms table.
    
    OBSERVABILITY: Logs all steps
    TRACEABILITY: Tracks migration progress
    EVALUATION: Verifies success
    """
    print("[TRACE] Starting room visibility migration...")
    
    db_path = "data.sqlite.db"
    
    try:
        # Connect to database
        print(f"[TRACE] Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        print("[TRACE] Checking if is_public column exists...")
        cursor.execute("PRAGMA table_info(chat_rooms)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'is_public' in column_names:
            print("[EVAL] Column 'is_public' already exists - skipping migration")
            conn.close()
            return True
        
        # Add column (default FALSE = hidden/private)
        print("[TRACE] Adding is_public column (default FALSE = hidden)...")
        cursor.execute("""
            ALTER TABLE chat_rooms 
            ADD COLUMN is_public BOOLEAN DEFAULT 0 NOT NULL
        """)
        
        # EVALUATION: Verify column was added
        cursor.execute("PRAGMA table_info(chat_rooms)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'is_public' not in column_names:
            raise Exception("Column was not added successfully")
        
        print("[EVAL] Column added successfully")
        
        # Commit changes
        conn.commit()
        print("[TRACE] Migration committed")
        
        # Close connection
        conn.close()
        print("[TRACE] Database connection closed")
        
        print("\n" + "="*60)
        print("✅ MIGRATION SUCCESS")
        print("="*60)
        print("Added: is_public BOOLEAN (default FALSE)")
        print("Effect: All existing rooms are now 'hidden' (invite-only)")
        print("Note: Set is_public=TRUE for discoverable rooms")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print("[ERROR] Rolling back...")
        try:
            conn.rollback()
            conn.close()
        except:
            pass
        return False


if __name__ == "__main__":
    """Run migration directly: python migrations/add_room_visibility.py"""
    success = run_migration()
    sys.exit(0 if success else 1)
