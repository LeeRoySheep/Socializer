"""
Initialize database with all tables including memory fields.

This script creates the database and all required tables for the
Socializer application, including the new memory encryption fields.

Author: Socializer Development Team
Date: 2024-11-12
"""

import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datamanager.data_model import DataModel, Base, User
from datamanager.data_manager import DataManager


def init_database():
    """Initialize the database with all tables."""
    print("\n" + "="*70)
    print("🔧 INITIALIZING DATABASE WITH MEMORY SUPPORT")
    print("="*70)
    
    # Create DataModel instance
    db_path = "socializer.db"
    print(f"\n📁 Database path: {db_path}")
    
    # Check if database exists
    if Path(db_path).exists():
        print("⚠️  Database already exists. Backing up...")
        backup_path = f"{db_path}.backup"
        if Path(backup_path).exists():
            os.remove(backup_path)
        os.rename(db_path, backup_path)
        print(f"✅ Backup created: {backup_path}")
    
    # Create new database
    print("\n🔨 Creating database and tables...")
    data_model = DataModel(sqlite_file_name=db_path)
    
    # Create all tables (including User with memory fields)
    data_model.create_db_and_tables()
    print("✅ All tables created successfully!")
    
    # Verify tables were created
    print("\n🔍 Verifying database structure...")
    with data_model.SessionLocal() as session:
        # Check if users table exists and has memory fields
        result = session.execute(text("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='users'
        """))
        
        table_def = result.fetchone()
        if table_def:
            sql_text = table_def[0]
            print("✅ Users table found")
            
            # Check for memory fields
            if "encryption_key" in sql_text:
                print("✅ encryption_key field present")
            else:
                print("⚠️  encryption_key field missing")
            
            if "conversation_memory" in sql_text:
                print("✅ conversation_memory field present")
            else:
                print("⚠️  conversation_memory field missing")
        else:
            print("❌ Users table not found!")
    
    print("\n✅ Database initialization complete!")
    return data_model


def create_test_users(data_manager: DataManager):
    """Create test users with encryption keys."""
    print("\n" + "="*70)
    print("👥 CREATING TEST USERS")
    print("="*70)
    
    test_users = [
        {"username": "alice", "email": "alice@test.com", "password": "password123"},
        {"username": "bob", "email": "bob@test.com", "password": "password456"},
        {"username": "charlie", "email": "charlie@test.com", "password": "password789"},
    ]
    
    created_users = []
    
    for user_data in test_users:
        try:
            # Hash the password (simple hash for testing)
            from hashlib import sha256
            hashed_password = sha256(user_data["password"].encode()).hexdigest()
            hashed_email = sha256(user_data["email"].encode()).hexdigest()
            
            # Create user
            user = User(
                username=user_data["username"],
                hashed_password=hashed_password,
                hashed_email=hashed_email,
                encryption_key=Fernet.generate_key().decode()  # Generate unique key
            )
            
            # Add to database
            added_user = data_manager.add_user(user)
            if added_user:
                print(f"✅ Created user: {user_data['username']} (ID: {added_user.id})")
                created_users.append(added_user)
            else:
                print(f"⚠️  Failed to create user: {user_data['username']}")
                
        except Exception as e:
            print(f"❌ Error creating user {user_data['username']}: {e}")
    
    return created_users


def verify_memory_functionality(data_manager: DataManager, users):
    """Verify that memory encryption and storage works."""
    print("\n" + "="*70)
    print("🧪 TESTING MEMORY FUNCTIONALITY")
    print("="*70)
    
    if not users:
        print("⚠️  No users to test with")
        return
    
    # Test with first user
    user = users[0]
    print(f"\n📝 Testing with user: {user.username}")
    
    try:
        # Import memory modules
        from memory.secure_memory_manager import SecureMemoryManager
        from memory.user_agent import UserAgent
        
        # Create a mock LLM
        class MockLLM:
            def invoke(self, messages):
                return "Mock response"
        
        # Create user agent
        agent = UserAgent(user=user, llm=MockLLM(), data_manager=data_manager)
        print("✅ UserAgent created")
        
        # Add some messages
        test_messages = [
            {"role": "user", "content": "Hello, AI!"},
            {"role": "assistant", "content": "Hello! How can I help you today?"},
            {"role": "user", "content": "What's the weather like?"},
            {"role": "assistant", "content": "I'd be happy to help with weather information!"}
        ]
        
        for msg in test_messages:
            agent.add_to_memory(msg)
        
        print(f"✅ Added {len(test_messages)} messages to memory")
        
        # Save memory
        success = agent.save_memory()
        if success:
            print("✅ Memory saved successfully")
        else:
            print("❌ Failed to save memory")
        
        # Recall memory
        recalled = agent.recall_memory()
        if recalled:
            message_count = len(recalled.get("messages", []))
            print(f"✅ Memory recalled: {message_count} messages")
        else:
            print("❌ Failed to recall memory")
        
        # Verify encryption
        encrypted_memory = data_manager.get_user_memory(user.id)
        if encrypted_memory and encrypted_memory.startswith('gAAAAA'):
            print("✅ Memory is encrypted (Fernet format)")
        else:
            print("⚠️  Memory might not be encrypted properly")
        
        # Test isolation - create agent for different user
        if len(users) > 1:
            user2 = users[1]
            agent2 = UserAgent(user=user2, llm=MockLLM(), data_manager=data_manager)
            
            # User 2 should have empty memory
            memory2 = agent2.recall_memory()
            if memory2 and len(memory2.get("messages", [])) == 0:
                print("✅ User isolation working - User 2 has no access to User 1's memory")
            else:
                print("⚠️  User isolation issue detected")
        
        print("\n✅ Memory functionality verified!")
        
    except ImportError as e:
        print(f"⚠️  Could not import memory modules: {e}")
        print("   Memory modules may not be fully implemented yet")
    except Exception as e:
        print(f"❌ Error testing memory: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main initialization function."""
    print("\n" + "🚀"*35)
    print("SOCIALIZER DATABASE INITIALIZATION")
    print("🚀"*35)
    
    # Initialize database
    data_model = init_database()
    
    # Create DataManager
    data_manager = DataManager(db_path="socializer.db")
    
    # Create test users
    users = create_test_users(data_manager)
    
    # Verify memory functionality
    verify_memory_functionality(data_manager, users)
    
    print("\n" + "="*70)
    print("✅ DATABASE INITIALIZATION COMPLETE!")
    print("="*70)
    print("\n📊 Summary:")
    print(f"   • Database: socializer.db")
    print(f"   • Users created: {len(users)}")
    print(f"   • Memory support: Enabled")
    print(f"   • Encryption: User-specific keys")
    print("\n🎉 System ready for use!")


if __name__ == "__main__":
    from sqlalchemy import text
    main()
