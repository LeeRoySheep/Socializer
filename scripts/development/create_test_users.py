"""
Create Test Users for Private Room Testing

This script creates two test users if they don't exist.
"""

from datamanager.data_manager import DataManager
from datamanager.data_model import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_users():
    """Create test users for testing private rooms."""
    
    print("👥 Creating Test Users")
    print("=" * 60)
    
    dm = DataManager("data.sqlite.db")
    
    # Check if users exist
    user1 = dm.get_user_by_username("testuser1")
    user2 = dm.get_user_by_username("testuser2")
    
    if user1:
        print(f"   ℹ️  testuser1 already exists (ID: {user1.id})")
    else:
        print("   Creating testuser1...")
        hashed_password = pwd_context.hash("testpass123")
        new_user1 = User(
            username="testuser1",
            hashed_password=hashed_password,
            hashed_email=pwd_context.hash("testuser1@example.com"),
            role="user",
            temperature=0.7
        )
        created1 = dm.add_user(new_user1)
        if created1:
            print(f"   ✅ testuser1 created (ID: {created1.id})")
        else:
            print("   ❌ Failed to create testuser1")
    
    if user2:
        print(f"   ℹ️  testuser2 already exists (ID: {user2.id})")
    else:
        print("   Creating testuser2...")
        hashed_password = pwd_context.hash("testpass123")
        new_user2 = User(
            username="testuser2",
            hashed_password=hashed_password,
            hashed_email=pwd_context.hash("testuser2@example.com"),
            role="user",
            temperature=0.7
        )
        created2 = dm.add_user(new_user2)
        if created2:
            print(f"   ✅ testuser2 created (ID: {created2.id})")
        else:
            print("   ❌ Failed to create testuser2")
    
    print("\n" + "=" * 60)
    print("✅ Test users ready!")
    print("\nCredentials for both users:")
    print("   Username: testuser1 / testuser2")
    print("   Password: testpass123")
    print("\n✅ You can now run: python test_private_rooms.py")

if __name__ == "__main__":
    try:
        create_test_users()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
