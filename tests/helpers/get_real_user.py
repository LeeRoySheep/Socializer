"""
Helper script to fetch a real user from the database for testing.
This script will print the user details and generate a valid JWT token.
"""
import os
import sys
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth import create_access_token, get_user
from app.database import get_db

# Get a database session
db = next(get_db())

def get_user_token(username: str):
    """Get a user by username and generate a JWT token for them."""
    user = get_user(db, username)
    if not user:
        print(f"User '{username}' not found in the database.")
        return None
    
    # Generate a token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "email": user.hashed_email if hasattr(user, 'hashed_email') else ''
        },
        expires_delta=access_token_expires
    )
    
    return {
        "username": user.username,
        "user_id": user.id,
        "token": access_token,
        "expires_in": "30 minutes"
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Get a JWT token for a user')
    parser.add_argument('username', help='Username to generate token for')
    args = parser.parse_args()
    
    result = get_user_token(args.username)
    if result:
        print("\n" + "="*60)
        print(f"User: {result['username']} (ID: {result['user_id']})")
        print("-"*60)
        print(f"Token (expires in {result['expires_in']}):")
        print(result['token'])
        print("="*60 + "\n")
