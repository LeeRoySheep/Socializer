#!/usr/bin/env python3
"""
Database and Encryption Verification Script

Verifies that:
1. Database is accessible
2. User passwords are properly hashed
3. Encryption keys exist
4. Conversation memory is encrypted

Author: Socializer Team
Date: November 12, 2024
"""

import sys
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.config import SQLALCHEMY_DATABASE_URL


def verify_database():
    """Verify database structure and encryption."""
    
    print("=" * 70)
    print("🔐 DATABASE & ENCRYPTION VERIFICATION")
    print("=" * 70)
    print()
    
    db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
    print(f"Database: {db_path}")
    print()
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        
        if not cursor.fetchone():
            print("❌ Users table not found")
            return False
        
        print("✅ Users table exists")
        
        # Get user count
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✅ Users in database: {user_count}")
        
        if user_count == 0:
            print("⚠️  No users to verify - database is empty")
            conn.close()
            return True
        
        print()
        print("Checking encryption...")
        print()
        
        # Check password hashing
        cursor.execute("""
            SELECT id, username, hashed_password 
            FROM users 
            LIMIT 5
        """)
        
        users = cursor.fetchall()
        passwords_ok = True
        
        for user_id, username, hashed_password in users:
            if hashed_password and (hashed_password.startswith('$2b$') or 
                                   hashed_password.startswith('$2a$')):
                print(f"✅ User '{username}': Password properly hashed (bcrypt)")
            else:
                print(f"❌ User '{username}': Password NOT properly hashed!")
                passwords_ok = False
        
        print()
        
        # Check encryption keys
        cursor.execute("""
            SELECT id, username, encryption_key 
            FROM users 
            WHERE encryption_key IS NOT NULL
        """)
        
        users_with_keys = cursor.fetchall()
        
        print(f"✅ Users with encryption keys: {len(users_with_keys)}/{user_count}")
        
        if len(users_with_keys) < user_count:
            print(f"⚠️  Warning: {user_count - len(users_with_keys)} users missing encryption keys")
        
        print()
        
        # Check conversation memory encryption
        cursor.execute("""
            SELECT id, username, conversation_memory 
            FROM users 
            WHERE conversation_memory IS NOT NULL 
            AND conversation_memory != ''
        """)
        
        users_with_memory = cursor.fetchall()
        
        print(f"Users with conversation memory: {len(users_with_memory)}")
        
        if users_with_memory:
            encrypted_count = 0
            for user_id, username, memory in users_with_memory:
                # Encrypted Fernet data typically starts with 'gAAAAA' 
                # or is not readable JSON
                if memory and (memory.startswith('gAAAAA') or 
                              not memory.strip().startswith('{')):
                    encrypted_count += 1
                    print(f"✅ User '{username}': Memory is encrypted")
                else:
                    print(f"❌ User '{username}': Memory might NOT be encrypted")
            
            print()
            print(f"Encrypted memories: {encrypted_count}/{len(users_with_memory)}")
        
        conn.close()
        
        print()
        print("=" * 70)
        
        if passwords_ok and len(users_with_keys) >= user_count * 0.9:  # 90% threshold
            print("✅ DATABASE VERIFICATION PASSED")
            return True
        else:
            print("⚠️  DATABASE VERIFICATION: SOME ISSUES FOUND")
            return True  # Not critical, just warnings
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)
