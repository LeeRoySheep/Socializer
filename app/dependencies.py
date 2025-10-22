"""Dependencies for the application."""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from typing import Generator

from .database import SessionLocal
from .config import SECRET_KEY, ALGORITHM
from datamanager.data_model import User

# ✅ Import TokenManager for secure token handling
from app.auth import get_token_manager

# OAuth2 scheme for token authentication (optional - TokenManager handles it)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current user from the JWT token.
    
    ✅ Now uses TokenManager for secure, multi-method auth:
    - Checks Authorization header
    - Checks query parameter (?token=xxx)
    - Checks cookies
    
    Returns:
        User: The authenticated user object from database
    
    Raises:
        HTTPException: If token invalid or user not found
    """
    # ✅ Use TokenManager to validate token from any source
    token_manager = get_token_manager()
    
    try:
        # This automatically checks header, query, and cookie
        token_data = token_manager.validate_request(request)
        
        # Get user from database
        user = db.query(User).filter(User.username == token_data.username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # ✅ Return the actual User object (not just username string!)
        return user
        
    except HTTPException as e:
        # Re-raise HTTP exceptions (like 401 from TokenManager)
        raise e
    except Exception as e:
        # Catch any other errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
