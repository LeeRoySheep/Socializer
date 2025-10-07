"""
Helper script to set up test users for WebSocket testing.
"""
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, SessionLocal
from app.auth import get_password_hash
from datamanager.data_model import User

def create_test_user(db, username: str, user_id: int, password: str = "testpass123"):
    """Create a test user if they don't exist."""
    # Check if user already exists
    user = db.query(User).filter(User.username == username).first()
    if user:
        print(f"User '{username}' already exists (ID: {user.id})")
        # Update user with new password and ensure they're active
        user.hashed_password = get_password_hash(password)
        user.is_active = True
        db.commit()
        db.refresh(user)
        return user
    
    # Create new user
    hashed_password = get_password_hash(password)
    user = User(
        id=user_id,
        username=username,
        hashed_password=hashed_password,
        hashed_email=f"{username}@example.com",
        is_active=True,
        member_since=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    print(f"✅ Created user: {username} (ID: {user.id})")
    return user

def setup_test_users():
    """Set up test users for WebSocket testing."""
    db = SessionLocal()
    try:
        # Create test users with high IDs to avoid conflicts
        users = [
            {"username": "testuser", "user_id": 1001},
            {"username": "testuser2", "user_id": 1002},
            {"username": "testuser3", "user_id": 1003}
        ]
        
        created_users = []
        for user_data in users:
            user = create_test_user(db, **user_data)
            created_users.append(user)
            
        return created_users
    except Exception as e:
        print(f"❌ Error setting up test users: {str(e)}")
        db.rollback()
        return []
    finally:
        db.close()

if __name__ == "__main__":
    print("Setting up test users...")
    setup_test_users()
