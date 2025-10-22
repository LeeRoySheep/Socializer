#!/usr/bin/env python3
"""
Script to create a test user in the database.
"""
import sys
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext

# Import your database models
sys.path.append('/Users/leeroystevenson/PycharmProjects/Socializer')
from datamanager.data_model import User, Base
from app.config import SQLALCHEMY_DATABASE_URL

# Create database engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user(username: str, email: str, password: str) -> bool:
    """Create a test user in the database."""
    try:
        # Create a new session
        with Session(engine) as session:
            # Check if user already exists
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                print(f"User with username '{username}' or email '{email}' already exists.")
                return False
            
            # Create new user
            hashed_password = pwd_context.hash(password)
            new_user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False
            )
            
            session.add(new_user)
            session.commit()
            print(f"Successfully created user: {username}")
            return True
            
    except SQLAlchemyError as e:
        print(f"Database error: {e}")
        session.rollback()
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <username> <email> <password>")
        print(f"Example: {sys.argv[0]} testuser test@example.com testpass123")
        sys.exit(1)
        
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    if create_user(username, email, password):
        print(f"\nYou can now log in with:")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print("\nTest the login with:")
        print(f"python scripts/test_auth.py {username} {password}")
    else:
        print("Failed to create user.")
        sys.exit(1)
