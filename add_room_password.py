"""
Add password column to chat_rooms table

This migration adds optional password protection to rooms.
"""

import sqlite3

def add_password_column():
    """Add password column to chat_rooms table."""
    print("🔄 Adding password column to chat_rooms table...")
    
    conn = sqlite3.connect("data.sqlite.db")
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(chat_rooms)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'password' in columns:
            print("   ℹ️  Password column already exists")
            return
        
        # Add password column
        cursor.execute("ALTER TABLE chat_rooms ADD COLUMN password VARCHAR")
        conn.commit()
        
        print("   ✅ Password column added successfully")
        print("\n✅ Migration complete!")
        print("   Rooms can now have optional password protection")
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    add_password_column()
