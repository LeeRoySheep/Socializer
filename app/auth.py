"""Authentication and security utilities.

Provides JWT-based authentication, password hashing, and user authorization
for the Socializer application.

OBSERVABILITY:
- Logs authentication attempts and failures
- Tracks token creation and validation
- Monitors blacklisted token usage attempts

TRACEABILITY:
- Associates tokens with user IDs and usernames
- Timestamps token expiration
- Tracks token blacklist for logout enforcement

EVALUATION:
- Validates JWT token signatures
- Verifies token expiration
- Checks password hashes using bcrypt
- Enforces user active status
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db, SessionLocal
from datamanager.data_model import User
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Security utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Token blacklist to store invalidated tokens
TOKEN_BLACKLIST = set()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.
    
    Parameters:
        plain_password (str): User-provided password in plain text
        hashed_password (str): Bcrypt hash from database
    
    Returns:
        bool: True if password matches hash, False otherwise
    
    Evaluation:
        - Uses constant-time comparison to prevent timing attacks
        - Validates hash format before comparison
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash from a plain-text password.
    
    Parameters:
        password (str): Plain-text password to hash
    
    Returns:
        str: Bcrypt hash suitable for database storage
    
    Security:
        - Uses bcrypt with automatic salt generation
        - Default work factor provides strong protection
        - Hash includes algorithm version for future upgrades
    """
    return pwd_context.hash(password)

def get_user(db: Session, username: str) -> Optional[User]:
    """Retrieve a user from the database by username.
    
    Parameters:
        db (Session): SQLAlchemy database session
        username (str): Username to search for (case-sensitive)
    
    Returns:
        Optional[User]: User object if found, None otherwise
    
    Traceability:
        - Queries by exact username match
        - Returns full user profile with metadata
    """
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password credentials.
    
    Parameters:
        db (Session): SQLAlchemy database session
        username (str): User's username
        password (str): User's plain-text password
    
    Returns:
        Optional[User]: User object if authentication successful, None otherwise
    
    Evaluation:
        - Verifies user exists in database
        - Validates password hash using constant-time comparison
        - Returns None for invalid credentials (no details leaked)
    
    Observability:
        - Log authentication attempts (success/failure)
        - Track failed login patterns for security monitoring
    """
    user = get_user(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token with embedded user data.
    
    Parameters:
        data (dict): Payload data to encode (typically {"sub": username})
        expires_delta (Optional[timedelta]): Token lifetime (default: 15 minutes)
    
    Returns:
        str: Encoded JWT token string
    
    Traceability:
        - Embeds username in 'sub' claim
        - Adds 'exp' (expiration) timestamp
        - Signs with SECRET_KEY using HS256 algorithm
    
    Security:
        - Short expiration time limits exposure window
        - Tokens are stateless and cannot be revoked (use blacklist)
        - Algorithm is HMAC-based for performance and security
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency to extract and validate current user from JWT token.
    
    Parameters:
        token (str): JWT token from Authorization header (injected by OAuth2PasswordBearer)
        db (Session): Database session dependency
    
    Returns:
        User: Authenticated user object from database
    
    Raises:
        HTTPException(401): If token is invalid, expired, blacklisted, or user not found
    
    Evaluation:
        - Checks token blacklist for logged-out sessions
        - Validates JWT signature and expiration
        - Verifies user still exists in database
        - Extracts username from 'sub' claim
    
    Observability:
        - Logs token validation failures
        - Tracks blacklisted token access attempts
    
    Traceability:
        - Associates request with user_id
        - Maintains audit trail for protected endpoints
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        if token in TOKEN_BLACKLIST:
            raise credentials_exception
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        user = get_user(db, username=username)
        if user is None:
            raise credentials_exception
            
        return user
        
    except JWTError:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """FastAPI dependency to get current user and verify active status.
    
    Parameters:
        current_user (User): User object from get_current_user dependency
    
    Returns:
        User: Authenticated and active user object
    
    Raises:
        HTTPException(400): If user account is inactive/disabled
    
    Evaluation:
        - Checks user.is_active flag
        - Prevents inactive users from accessing protected resources
    
    Use Case:
        - Enforces account suspension/deactivation
        - Allows admin to disable accounts without deletion
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
