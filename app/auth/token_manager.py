"""
Token Manager - Secure Token Handling
======================================

Centralized, secure token management following OOP and security best practices.

Author: AI Assistant
Date: 2025-10-22
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer


class TokenConfig:
    """Token configuration with security best practices."""
    
    # Load from environment with secure defaults
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Cookie settings
    COOKIE_NAME: str = "access_token"
    COOKIE_SECURE: bool = os.getenv("ENVIRONMENT", "development") == "production"
    COOKIE_HTTP_ONLY: bool = True
    COOKIE_SAME_SITE: str = "lax"
    COOKIE_MAX_AGE: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    
    # Token prefix
    TOKEN_PREFIX: str = "Bearer "


class TokenData:
    """Token data model."""
    
    def __init__(self, username: str, user_id: Optional[int] = None, **extras):
        self.username = username
        self.user_id = user_id
        self.extras = extras
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        data = {"sub": self.username}
        if self.user_id:
            data["user_id"] = self.user_id
        data.update(self.extras)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenData":
        """Create from dictionary (JWT payload)."""
        username = data.get("sub")
        user_id = data.get("user_id")
        extras = {k: v for k, v in data.items() if k not in ("sub", "user_id", "exp", "iat")}
        return cls(username=username, user_id=user_id, **extras)


class TokenManager:
    """
    Centralized token management with security best practices.
    
    Features:
    - Secure token creation and validation
    - Multiple token retrieval methods (cookie, header, query)
    - Automatic expiration handling
    - Cookie management
    - Comprehensive error handling
    
    Usage:
    ------
    ```python
    # Create token manager
    token_manager = TokenManager()
    
    # Create token
    token = token_manager.create_token(
        username="john",
        user_id=123,
        expires_minutes=30
    )
    
    # Validate token
    token_data = token_manager.validate_token(token)
    
    # Get token from request
    token = token_manager.get_token_from_request(request)
    ```
    """
    
    def __init__(self, config: Optional[TokenConfig] = None):
        """
        Initialize TokenManager.
        
        Parameters:
        -----------
        config : Optional[TokenConfig]
            Token configuration. Uses defaults if not provided.
        """
        self.config = config or TokenConfig()
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
    
    def create_token(
        self,
        username: str,
        user_id: Optional[int] = None,
        expires_minutes: Optional[int] = None,
        **extra_claims
    ) -> str:
        """
        Create a new JWT token.
        
        Parameters:
        -----------
        username : str
            Username to encode in token
        user_id : Optional[int]
            User ID to encode in token
        expires_minutes : Optional[int]
            Token expiration in minutes (uses config default if not provided)
        **extra_claims
            Additional claims to include in token
        
        Returns:
        --------
        str
            Encoded JWT token
        """
        # Create token data
        token_data = TokenData(username=username, user_id=user_id, **extra_claims)
        to_encode = token_data.to_dict()
        
        # Add expiration
        expires_delta = timedelta(
            minutes=expires_minutes or self.config.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        expire = datetime.now(timezone.utc) + expires_delta
        to_encode["exp"] = expire
        to_encode["iat"] = datetime.now(timezone.utc)
        
        # Encode token
        encoded_jwt = jwt.encode(
            to_encode,
            self.config.SECRET_KEY,
            algorithm=self.config.ALGORITHM
        )
        
        return encoded_jwt
    
    def validate_token(self, token: str) -> TokenData:
        """
        Validate and decode a JWT token.
        
        Parameters:
        -----------
        token : str
            JWT token to validate
        
        Returns:
        --------
        TokenData
            Decoded token data
        
        Raises:
        -------
        HTTPException
            If token is invalid or expired
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # Remove Bearer prefix if present
            if token.startswith(self.config.TOKEN_PREFIX):
                token = token[len(self.config.TOKEN_PREFIX):]
            
            # Decode token
            payload = jwt.decode(
                token,
                self.config.SECRET_KEY,
                algorithms=[self.config.ALGORITHM],
                options={"verify_exp": True}
            )
            
            # Extract data
            token_data = TokenData.from_dict(payload)
            
            if not token_data.username:
                raise credentials_exception
            
            return token_data
            
        except JWTError as e:
            print(f"JWT validation error: {e}")
            raise credentials_exception
    
    def get_token_from_request(self, request: Request) -> Optional[str]:
        """
        Extract token from request (multiple methods).
        
        Priority:
        1. Authorization header (Bearer token)
        2. Query parameter (?token=xxx)
        3. Cookie
        
        Parameters:
        -----------
        request : Request
            FastAPI request object
        
        Returns:
        --------
        Optional[str]
            Token if found, None otherwise
        """
        # Method 1: Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith(self.config.TOKEN_PREFIX):
            token = auth_header[len(self.config.TOKEN_PREFIX):]
            if token:
                return token
        
        # Method 2: Query parameter
        token = request.query_params.get("token")
        if token:
            return token
        
        # Method 3: Cookie
        cookie_value = request.cookies.get(self.config.COOKIE_NAME)
        if cookie_value:
            # Remove Bearer prefix if present in cookie
            if cookie_value.startswith(self.config.TOKEN_PREFIX):
                return cookie_value[len(self.config.TOKEN_PREFIX):]
            return cookie_value
        
        return None
    
    def validate_request(self, request: Request) -> TokenData:
        """
        Validate token from request.
        
        Parameters:
        -----------
        request : Request
            FastAPI request object
        
        Returns:
        --------
        TokenData
            Validated token data
        
        Raises:
        -------
        HTTPException
            If no token found or token invalid
        """
        token = self.get_token_from_request(request)
        
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return self.validate_token(token)
    
    def set_token_cookie(
        self,
        response: Response,
        token: str,
        expires_minutes: Optional[int] = None
    ):
        """
        Set token as HTTP-only cookie.
        
        Parameters:
        -----------
        response : Response
            FastAPI response object
        token : str
            JWT token to set
        expires_minutes : Optional[int]
            Cookie expiration in minutes
        """
        response.set_cookie(
            key=self.config.COOKIE_NAME,
            value=f"{self.config.TOKEN_PREFIX}{token}",
            max_age=expires_minutes * 60 if expires_minutes else self.config.COOKIE_MAX_AGE,
            httponly=self.config.COOKIE_HTTP_ONLY,
            secure=self.config.COOKIE_SECURE,
            samesite=self.config.COOKIE_SAME_SITE,
            path="/"
        )
    
    def clear_token_cookie(self, response: Response):
        """
        Clear token cookie (logout).
        
        Parameters:
        -----------
        response : Response
            FastAPI response object
        """
        response.delete_cookie(
            key=self.config.COOKIE_NAME,
            path="/"
        )
    
    def refresh_token(self, old_token: str) -> str:
        """
        Refresh an existing token (extends expiration).
        
        Parameters:
        -----------
        old_token : str
            Current token to refresh
        
        Returns:
        --------
        str
            New token with extended expiration
        
        Raises:
        -------
        HTTPException
            If token is invalid
        """
        # Validate old token
        token_data = self.validate_token(old_token)
        
        # Create new token with same data
        return self.create_token(
            username=token_data.username,
            user_id=token_data.user_id,
            **token_data.extras
        )


# Global instance for easy access
_default_token_manager = None

def get_token_manager() -> TokenManager:
    """
    Get the default TokenManager instance (singleton).
    
    Returns:
    --------
    TokenManager
        Global token manager instance
    """
    global _default_token_manager
    if _default_token_manager is None:
        _default_token_manager = TokenManager()
    return _default_token_manager
