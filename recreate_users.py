#!/usr/bin/env python3
"""
Recreate User Database
======================
Recreates the lost user database with proper users.
"""

from datamanager.data_manager import DataManager
from datamanager.data_model import User
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database
dm = DataManager('data.sqlite.db')

# Users to create - All test users with same password
COMMON_PASSWORD = "FuckShit123."

users_to_create = [
    # Leroy variants
    {"username": "Leroy", "email": "leroy@socializer.com"},
    {"username": "Leroy2", "email": "leroy2@socializer.com"},
    
    # Human variants by language
    {"username": "human2", "email": "human2@socializer.com"},
    {"username": "humanEsp", "email": "humanesp@socializer.com"},
    {"username": "humanDe", "email": "humande@socializer.com"},
    {"username": "humanFr", "email": "humanfr@socializer.com"},
    {"username": "humanIt", "email": "humanit@socializer.com"},
    {"username": "humanEn", "email": "humanen@socializer.com"},
    
    # Test users
    {"username": "testuser", "email": "test@socializer.com"},
    {"username": "demo", "email": "demo@socializer.com"},
]

print("🔧 Recreating Users...")
print("=" * 60)

# Clear existing users first
with dm.get_session() as session:
    session.query(User).delete()
    session.commit()
    print("✅ Cleared existing users\n")

# Create new users
for user_data in users_to_create:
    print(f"Creating user: {user_data['username']}...")
    
    # Hash password (same for all users)
    hashed_password = pwd_context.hash(COMMON_PASSWORD)
    
    # Generate encryption key
    encryption_key = Fernet.generate_key().decode('utf-8')
    
    # Hash email for privacy
    hashed_email = pwd_context.hash(user_data['email'])
    
    # Create user with ALL required fields from data_model.py
    user = User(
        username=user_data['username'],
        hashed_password=hashed_password,
        hashed_email=hashed_email,
        hashed_name="",  # Privacy: no name stored
        encryption_key=encryption_key,
        is_active=True,
        role="user",
        temperature=0.7,  # Default AI temperature
        preferences={},  # Empty preferences dict
        messages=0  # Message count starts at 0
    )
    
    # Add to database
    created_user = dm.add_user(user)
    if created_user:
        print(f"  ✅ Created: {created_user.username} (ID: {created_user.id})")
        print(f"     Email: {user_data['email']}")
        print(f"     Encryption: Enabled ✅")
    else:
        print(f"  ❌ Failed to create {user_data['username']}")
    print()

print("\n" + "=" * 60)
print("✅ User recreation complete!")
print(f"\n🔑 ALL users have the same password: {COMMON_PASSWORD}")
print(f"🔒 All user data is encrypted with individual Fernet keys")
print("\nAvailable users:")
for user in users_to_create:
    print(f"  • {user['username']}")
