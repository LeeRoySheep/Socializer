from datetime import datetime, timedelta
from typing import Optional
import json
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datamanager.data_model import User
from app.database import get_db

# JWT settings (must match main.py)
SECRET_KEY = "your-secret-key-here"  # Change this to a secure secret key in production
ALGORITHM = "HS256"

def get_current_user_websocket(token: str, db: Session) -> Optional[User]:
    """
    Get current user from JWT token for WebSocket connections.
    This is similar to get_current_user but for WebSocket endpoints.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = {"username": username}
    except JWTError:
        return None
    
    user = db.query(User).filter(User.username == token_data["username"]).first()
    if user is None:
        return None
    return user
