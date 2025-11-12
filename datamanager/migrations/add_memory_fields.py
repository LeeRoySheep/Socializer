"""
Database migration to add memory-related fields to User table.

This migration adds:
1. encryption_key: User-specific encryption key for memory
2. conversation_memory: Encrypted conversation memory storage

Author: Socializer Development Team
Date: 2024-11-12
"""

from sqlalchemy import text
from cryptography.fernet import Fernet


def upgrade(engine):
    """
    Add memory fields to users table.
    """
    with engine.connect() as conn:
        # Add encryption_key column
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN encryption_key VARCHAR(255)
            """))
            print("✅ Added encryption_key column to users table")
        except Exception as e:
            print(f"⚠️ encryption_key column may already exist: {e}")
        
        # Add conversation_memory column (TEXT for large encrypted data)
        try:
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN conversation_memory TEXT
            """))
            print("✅ Added conversation_memory column to users table")
        except Exception as e:
            print(f"⚠️ conversation_memory column may already exist: {e}")
        
        # Generate encryption keys for existing users
        try:
            # Get all users without encryption keys
            result = conn.execute(text("""
                SELECT id FROM users 
                WHERE encryption_key IS NULL OR encryption_key = ''
            """))
            
            users = result.fetchall()
            
            for user in users:
                # Generate unique encryption key for each user
                key = Fernet.generate_key().decode()
                
                # Update user with new key
                conn.execute(
                    text("""
                        UPDATE users 
                        SET encryption_key = :key 
                        WHERE id = :user_id
                    """),
                    {"key": key, "user_id": user[0]}
                )
            
            print(f"✅ Generated encryption keys for {len(users)} existing users")
            
        except Exception as e:
            print(f"❌ Error generating encryption keys: {e}")
        
        conn.commit()


def downgrade(engine):
    """
    Remove memory fields from users table.
    """
    with engine.connect() as conn:
        try:
            conn.execute(text("""
                ALTER TABLE users 
                DROP COLUMN encryption_key
            """))
            print("✅ Removed encryption_key column")
        except Exception as e:
            print(f"⚠️ Error removing encryption_key: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE users 
                DROP COLUMN conversation_memory
            """))
            print("✅ Removed conversation_memory column")
        except Exception as e:
            print(f"⚠️ Error removing conversation_memory: {e}")
        
        conn.commit()


if __name__ == "__main__":
    # Run migration when executed directly
    from sqlalchemy import create_engine
    import os
    
    # Get database path
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "socializer.db"
    )
    
    # Create engine
    engine = create_engine(f"sqlite:///{db_path}")
    
    # Run upgrade
    print("\n🔄 Running memory fields migration...")
    upgrade(engine)
    print("✅ Migration complete!")
    
    # Dispose of engine
    engine.dispose()
