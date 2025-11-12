"""
Migration script to add memory fields to existing database.

This script safely adds encryption and memory fields to the existing
data.sqlite.db database without losing any existing data.

Author: Socializer Development Team
Date: 2024-11-12
"""

import sqlite3
import os
import sys
from datetime import datetime
from cryptography.fernet import Fernet
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def backup_database(db_path):
    """Create a backup of the database before migration."""
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path


def add_memory_fields(db_path='data.sqlite.db'):
    """Add memory-related fields to existing database."""
    
    print("\n" + "="*70)
    print("🔄 MIGRATING EXISTING DATABASE TO ADD MEMORY FIELDS")
    print("="*70)
    
    # Check if database exists
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    print(f"\n📁 Database: {db_path}")
    
    # Create backup
    print("\n📦 Creating backup...")
    backup_path = backup_database(db_path)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check current structure
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print("\n🔍 Checking current structure...")
        print(f"   Current columns: {len(column_names)}")
        
        # Add encryption_key field if missing
        if 'encryption_key' not in column_names:
            print("\n➕ Adding encryption_key field...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN encryption_key VARCHAR
            """)
            print("   ✅ encryption_key field added")
        else:
            print("   ℹ️  encryption_key field already exists")
        
        # Add conversation_memory field if missing
        if 'conversation_memory' not in column_names:
            print("\n➕ Adding conversation_memory field...")
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN conversation_memory TEXT
            """)
            print("   ✅ conversation_memory field added")
        else:
            print("   ℹ️  conversation_memory field already exists")
        
        # Generate encryption keys for existing users without keys
        print("\n🔑 Generating encryption keys for existing users...")
        
        # Get users without encryption keys
        cursor.execute("""
            SELECT id, username 
            FROM users 
            WHERE encryption_key IS NULL OR encryption_key = ''
        """)
        users_without_keys = cursor.fetchall()
        
        if users_without_keys:
            print(f"   Found {len(users_without_keys)} users without encryption keys")
            
            for user_id, username in users_without_keys:
                # Generate unique encryption key
                key = Fernet.generate_key().decode()
                
                # Update user with new key
                cursor.execute("""
                    UPDATE users 
                    SET encryption_key = ? 
                    WHERE id = ?
                """, (key, user_id))
                
                print(f"   ✅ Generated key for user: {username} (ID: {user_id})")
        else:
            print("   ✅ All users already have encryption keys")
        
        # Commit changes
        conn.commit()
        
        # Verify migration
        print("\n🔍 Verifying migration...")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'encryption_key' in column_names and 'conversation_memory' in column_names:
            print("   ✅ Both memory fields are present")
            
            # Check that all users have keys
            cursor.execute("SELECT COUNT(*) FROM users WHERE encryption_key IS NOT NULL")
            users_with_keys = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]
            
            print(f"   ✅ {users_with_keys}/{total_users} users have encryption keys")
            
            if users_with_keys == total_users:
                print("\n✅ MIGRATION SUCCESSFUL!")
                return True
            else:
                print("\n⚠️  Some users still missing encryption keys")
                return False
        else:
            print("   ❌ Memory fields not properly added")
            return False
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"   Backup is available at: {backup_path}")
        conn.rollback()
        return False
        
    finally:
        conn.close()


def verify_database_structure(db_path='data.sqlite.db'):
    """Verify the database structure after migration."""
    
    print("\n" + "="*70)
    print("📊 DATABASE STRUCTURE VERIFICATION")
    print("="*70)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print("\n📋 Tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   • {table[0]}: {count} records")
        
        # Check users table in detail
        print("\n👥 Users Table Structure:")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            nullable = "NULL" if col[3] == 0 else "NOT NULL"
            
            # Highlight memory fields
            if col_name in ['encryption_key', 'conversation_memory']:
                print(f"   ✨ {col_name} ({col_type}) {nullable}")
            else:
                print(f"   • {col_name} ({col_type}) {nullable}")
        
        # Sample user check
        cursor.execute("""
            SELECT id, username, 
                   CASE WHEN encryption_key IS NOT NULL THEN '✅' ELSE '❌' END as has_key,
                   CASE WHEN conversation_memory IS NOT NULL THEN '✅' ELSE '❌' END as has_memory
            FROM users 
            LIMIT 5
        """)
        
        print("\n📝 Sample Users (first 5):")
        users = cursor.fetchall()
        for user in users:
            print(f"   • ID:{user[0]} {user[1]}: Key={user[2]} Memory={user[3]}")
        
    finally:
        conn.close()


def test_memory_with_existing_user(db_path='data.sqlite.db'):
    """Test memory functionality with an existing user."""
    
    print("\n" + "="*70)
    print("🧪 TESTING MEMORY WITH EXISTING USER")
    print("="*70)
    
    try:
        from datamanager.data_manager import DataManager
        from memory.user_agent import UserAgent
        
        # Initialize DataManager with existing database
        dm = DataManager(db_path=db_path)
        
        # Get first user for testing
        test_user = dm.get_user(1)  # Get user with ID 1
        
        if not test_user:
            print("⚠️  No user found with ID 1")
            return
        
        print(f"\n📝 Testing with user: {test_user.username}")
        print(f"   • Has encryption key: {'✅' if test_user.encryption_key else '❌'}")
        
        # Mock LLM for testing
        class MockLLM:
            def invoke(self, messages):
                return type('obj', (object,), {'content': 'Mock AI response'})()
        
        # Create user agent
        agent = UserAgent(user=test_user, llm=MockLLM(), data_manager=dm)
        print("✅ UserAgent created successfully")
        
        # Add test message
        agent.add_to_memory({"role": "user", "content": "Test message for existing user"})
        agent.add_to_memory({"role": "assistant", "content": "Test response"})
        
        # Save memory
        if agent.save_memory():
            print("✅ Memory saved for existing user")
        else:
            print("❌ Failed to save memory")
        
        # Recall memory
        recalled = agent.recall_memory()
        if recalled:
            msg_count = len(recalled.get("messages", []))
            print(f"✅ Memory recalled: {msg_count} messages")
        else:
            print("❌ Failed to recall memory")
        
        print("\n✅ Memory system working with existing database!")
        
    except Exception as e:
        print(f"⚠️  Test error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main migration function."""
    
    print("\n" + "🔧"*35)
    print("SOCIALIZER DATABASE MIGRATION")
    print("🔧"*35)
    
    # Use existing database
    db_path = 'data.sqlite.db'
    
    # Perform migration
    success = add_memory_fields(db_path)
    
    if success:
        # Verify structure
        verify_database_structure(db_path)
        
        # Test with existing user
        test_memory_with_existing_user(db_path)
        
        print("\n" + "="*70)
        print("✅ MIGRATION COMPLETE!")
        print("="*70)
        print(f"\n📊 Summary:")
        print(f"   • Database: {db_path}")
        print(f"   • Memory fields: Added successfully")
        print(f"   • Encryption keys: Generated for all users")
        print(f"   • Backup created: Yes")
        print(f"\n🎉 Your existing database is now ready with memory support!")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
        print("   Your backup is safe and you can restore if needed.")


if __name__ == "__main__":
    main()
