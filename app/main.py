"""Main FastAPI application module."""
import json
import asyncio
import logging
import os
import time
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Union, Generator, Set

from pydantic import BaseModel

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.websockets import WebSocketState
from .models import User
from jose import JWTError, jwt, exceptions as jose_exceptions
from passlib.context import CryptContext
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Database imports
from .db import get_db
from datamanager.data_model import User, TokenBlacklist, ErrorLog, DataModel

# WebSocket imports
from app.websocket import router as websocket_router, ConnectionManager

# Initialize AI manager
from .ai_manager import AIAgentManager
ai_manager = AIAgentManager()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT settings
SECRET_KEY = "your-secret-key-here"  # Change this to a secure secret key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token blacklist to store invalidated tokens
TOKEN_BLACKLIST = set()

# Initialize WebSocket manager
manager = ConnectionManager()

# Password utilities
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Authentication utilities
def get_current_user(request: Request, db: Session) -> Optional[User]:
    """Get the current user from the JWT token in cookies or Authorization header."""
    try:
        # First try to get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            # Fall back to cookie
            token = request.cookies.get("access_token")
            if token and token.startswith("Bearer "):
                token = token[7:]  # Remove 'Bearer ' prefix
            else:
                print("No valid token found in Authorization header or cookies")
                return None
        
        # Check if token is blacklisted
        if token in TOKEN_BLACKLIST:
            print("Token is blacklisted")
            return None
            
        try:
            # Decode and verify token
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if not username:
                print("No username in token")
                return None
                
            # Get user from database
            user = db.query(User).filter(User.username == username).first()
            if not user:
                print(f"User {username} not found")
                return None
                
            if not getattr(user, 'is_active', True):
                print(f"User {username} is not active")
                return None
                
            return user
            
        except JWTError as e:
            print(f"JWT Error: {e}")
            return None
            
    except Exception as e:
        print(f"Unexpected error in get_current_user: {e}")
        return None

async def get_current_user_websocket(token: str, db: Session) -> Optional[User]:
    """Get the current user from a JWT token string (for WebSocket use)."""
    try:
        # Decode the JWT token directly
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            print(f"WebSocket auth failed: No username in token")
            return None
            
        # Look up user in database
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"WebSocket auth failed: User not found: {username}")
            return None
            
        return user
            
    except JWTError as e:
        print(f"WebSocket JWT Error: {e}")
        return None
        
    except Exception as e:
        print(f"WebSocket auth unexpected error: {e}")
        return None

async def get_current_active_user(
    request: Request, 
    db: Session = Depends(get_db)
) -> User:
    """Get the current active user from the JWT token in cookies."""
    current_user = get_current_user(request, db)
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not getattr(current_user, 'is_active', True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate a user with username and password."""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Import database utilities
from .db import get_db

# Import test runner router
from .routers import test_runner

# Initialize AI manager
from .ai_manager import AIAgentManager
ai_manager = AIAgentManager()

# Initialize FastAPI app
app = FastAPI(
    title="Socializer API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:63342",
        "http://127.0.0.1:63342",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5500"  # For live server testing
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=[
        "*",  # Allow all headers
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-CSRF-Token"
    ],
    expose_headers=[
        "Content-Length",
        "Set-Cookie",
        "Access-Control-Allow-Origin",
        "Access-Control-Allow-Credentials"
    ],
    max_age=600  # 10 minutes
)

# Include WebSocket routes
app.include_router(websocket_router, prefix="/ws")

# Include test runner router
app.include_router(test_runner.router, prefix="/tests")

# Include rooms router for private chat
from app.routers import rooms
app.include_router(rooms.router)

# WebSocket manager is already imported at the top
# Initialize WebSocket manager with database session
def get_connection_manager() -> ConnectionManager:
    """Get the WebSocket connection manager instance."""
    from app.websocket.chat_manager import manager
    return manager

connection_manager = get_connection_manager()

# Import User model
from datamanager.data_model import User

# Get the base directory of the project
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mount static files with absolute path
static_dir = os.path.join(BASE_DIR, 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates with absolute path
templates_dir = os.path.join(BASE_DIR, 'templates')
templates = Jinja2Templates(directory=templates_dir)

# Debug logging
print(f"[DEBUG] Static files directory: {static_dir}")
print(f"[DEBUG] Templates directory: {templates_dir}")
print(f"[DEBUG] Current working directory: {os.getcwd()}")

# Pydantic models for request/response
class ChatMessage(BaseModel):
    """Model for chat message requests."""
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Model for chat responses."""
    response: str
    conversation_id: str

class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    """Model for user creation."""
    username: str
    email: str
    password: str
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None
        }

# Authentication routes
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login endpoint to get an access token.
    
    - **username**: The user's username
    - **password**: The user's password
    
    Returns an access token that can be used for authenticated requests.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logout")
async def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Logout endpoint to clear the authentication cookie and invalidate the token.
    
    This adds the token to a blacklist to prevent further use.
    Returns a success message and clears the authentication cookie.
    """
    try:
        # Get the token from the Authorization header or cookie
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            token = request.cookies.get("access_token")
        
        # Add token to blacklist if it exists
        if token:
            if token.startswith("Bearer "):
                token = token[7:]  # Remove 'Bearer ' prefix
            # Add to blacklist with expiration time
            TOKEN_BLACKLIST.add(token)
            
            # Invalidate the token in the database (if you have such functionality)
            # This is where you'd add code to invalidate the token in your database
            
        # Create a response that will clear the cookie
        response = JSONResponse(
            content={"message": "Successfully logged out"},
            status_code=200
        )
        
        # Clear the access token cookie
        response.delete_cookie(
            key="access_token",
            httponly=True,
            samesite="lax",
            secure=False  # Set to True in production with HTTPS
        )
        
        # Also clear any other auth-related cookies
        response.delete_cookie("logged_in")
        
        # Clean up any remaining WebSocket connections for this user
        if hasattr(request.state, 'username'):
            username = request.state.username
            # Close WebSocket connection if exists
            if hasattr(request.state, 'websocket'):
                try:
                    await connection_manager.disconnect(request.state.websocket)
                except Exception as e:
                    logger.error(f"Error disconnecting WebSocket for {username}: {e}")
        
        return response
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return JSONResponse(
            content={"message": "Error during logout"},
            status_code=500
        )

# Pydantic models for responses
class UserResponse(BaseModel):
    """Pydantic model for user responses."""
    id: int
    username: str
    email: str
    is_active: bool
    role: str = "user"
    created_at: Optional[datetime] = None

# User routes
@app.get("/users/me/", response_model=UserResponse)
async def read_users_me(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get the current user's profile information.
    
    Returns:
        UserResponse: User profile information
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.hashed_email,  # Using hashed_email as that's the field in the User model
        is_active=getattr(current_user, 'is_active', True),
        role=getattr(current_user, 'role', 'user'),
        created_at=getattr(current_user, 'created_at', None),
        updated_at=getattr(current_user, 'updated_at', None)
    )


@app.get("/api/users/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all users (for inviting to rooms).
    
    Returns list of basic user information.
    """
    users = db.query(User).filter(User.is_active == True).all()
    
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.hashed_email,
            is_active=user.is_active,
            role=getattr(user, 'role', 'user'),
            created_at=getattr(user, 'created_at', None),
            updated_at=getattr(user, 'updated_at', None)
        )
        for user in users
    ]

# New Chat Interface

# Chat endpoints

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, current_user: User = Depends(get_current_active_user)):
    """
    Serve the chat interface.
    """
    try:
        # Get the user's information
        user_data = {
            "id": current_user.id,
            "username": current_user.username,
            "email": getattr(current_user, 'hashed_email', ''),  # Using hashed_email as that's the field in the User model
            "is_active": current_user.is_active,
            "created_at": getattr(current_user, 'member_since', None)  # Using member_since instead of created_at
        }
        
        # Get the token from the cookie
        token = request.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token[7:]
        
        # Render the chat template with user data
        return templates.TemplateResponse(
            "new-chat.html",
            {
                "request": request,
                "current_user": user_data,
                "user": user_data,  # Keep for backward compatibility
                "token": token,
                "access_token": token  # Also pass as access_token
            }
        )
    except Exception as e:
        logger.error(f"Error loading chat page: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error loading chat page"
        )
@app.post("/chat/", response_model=ChatResponse)
async def chat(
    chat_data: ChatMessage,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a chat message and return the AI's response.
    
    - **message**: The user's message (required)
    - **conversation_id**: Optional conversation ID for multi-turn conversations
    """
    # Here you would typically process the message with your AI model
    # For now, we'll just echo the message back
    return ChatResponse(
        response=f"You said: {chat_data.message}",
        conversation_id=chat_data.conversation_id or "default"
    )

# Test WebSocket endpoint for debugging
@app.websocket("/ws/test")
async def test_websocket(websocket: WebSocket):
    """Test WebSocket endpoint for debugging connection issues."""
    client_ip = websocket.client.host if websocket.client else 'unknown'
    print(f"[TEST_WS] New test connection from {client_ip}")
    
    try:
        await websocket.accept()
        print("[TEST_WS] Test WebSocket connection accepted")
        
        # Send a welcome message
        await websocket.send_json({
            "type": "test_response",
            "message": "Test WebSocket connection successful",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep the connection open for a while to test
        while True:
            try:
                # Wait for a message but don't block for too long
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                print(f"[TEST_WS] Received: {data}")
                await websocket.send_json({
                    "type": "echo",
                    "message": f"Echo: {data}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except asyncio.TimeoutError:
                # Send a keepalive message
                await websocket.send_json({
                    "type": "keepalive",
                    "message": "Still connected",
                    "timestamp": datetime.utcnow().isoformat()
                })
    except Exception as e:
        print(f"[TEST_WS] Error: {e}")
    finally:
        print("[TEST_WS] Test WebSocket connection closed")
        try:
            await websocket.close()
        except:
            pass

# Store connected users and their WebSocket connections
connected_users = {}
chat_sessions = {}  # Store chat sessions for each user

# Initialize AI Chatbot
from ai_chatagent import ChatSession
from ai_chatagent import ChatSession

# Store active chat sessions
chat_sessions = {}

def get_online_users():
    """Get a list of online usernames."""
    return list(connected_users.keys())

async def broadcast_user_list():
    """Broadcast the updated list of online users to all connected clients."""
    try:
        online_users = get_online_users()
        message = {
            "type": "user_list",
            "users": online_users,
            "timestamp": datetime.utcnow().isoformat()
        }
        await broadcast_message(message)
    except Exception as e:
        print(f"Error broadcasting user list: {e}")

async def broadcast_message(message: dict):
    """Broadcast a message to all connected clients."""
    for username in list(connected_users.keys()):
        for connection in connected_users[username]:
            try:
                if connection.client_state != WebSocketState.DISCONNECTED:
                    await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message to {username}: {e}")
                # Clean up dead connections
                if username in connected_users and connection in connected_users[username]:
                    connected_users[username].remove(connection)
                    if not connected_users[username]:
                        del connected_users[username]
                        # Clean up chat session if user is no longer connected
                        if username in chat_sessions:
                            del chat_sessions[username]

async def broadcast_user_joined(username: str):
    """Notify all users that a new user has joined."""
    message = {
        "type": "user_joined",
        "username": username,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"{username} has joined the chat"
    }
    
    for user_connections in connected_users.values():
        for websocket in user_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error notifying user joined: {e}")

async def broadcast_user_left(username: str):
    """Notify all users that a user has left."""
    message = {
        "type": "user_left",
        "username": username,
        "timestamp": datetime.utcnow().isoformat(),
        "message": f"{username} has left the chat"
    }
    
    for user_connections in connected_users.values():
        for websocket in user_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error notifying user left: {e}")

async def send_ai_response(username: str, message: str):
    """Generate and send an AI response to the chat."""
    try:
        # Get or create chat session for the user
        if username not in chat_sessions:
            try:
                from datamanager.data_model import User
                # Get or create user in the database
                with db_manager.SessionLocal() as db:
                    user = db.query(User).filter(User.username == username).first()
                    if not user:
                        # Create a new user if they don't exist
                        user = User(
                            username=username,
                            email=f"{username}@example.com",  # Temporary email
                            hashed_password="",  # No password for WebSocket users
                            is_active=True,
                            role="user"
                        )
                        db.add(user)
                        db.commit()
                        db.refresh(user)
                        print(f"Created new user: {username} (ID: {user.id})")
                        
                    # Initialize AI chat session with the user using AIAgentManager
                    try:
                        chat_sessions[username] = ai_manager.get_agent(user.id)
                        print(f"Initialized AI chat session for user: {username} with ID: {user.id}")
                    except Exception as e:
                        print(f"Error initializing AI chat session: {e}")
                        raise
            except Exception as e:
                print(f"Error initializing AI chat session: {e}")
                error_message = {
                    "type": "error",
                    "message": "Failed to initialize AI chat. Some features may not work.",
                    "timestamp": datetime.utcnow().isoformat()
                }
                await broadcast_message(error_message)
            
        # Get AI response
        try:
            print(f"Processing message with AI: {message}")
            ai_response = chat_sessions[username].process_message(message)
            print(f"AI response received: {ai_response}")
            
            # Ensure the response is a string
            if not isinstance(ai_response, str):
                print(f"Converting AI response to string. Original type: {type(ai_response)}")
                ai_response = str(ai_response)
                
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error processing AI message: {e}\n{error_trace}")
            ai_response = "I encountered an error while processing your request. Please try again."
            
            # Log the error to the database if possible
            try:
                with db_manager.SessionLocal() as db:
                    error_log = ErrorLog(
                        user_id=user.id if 'user' in locals() else None,
                        error_type=str(type(e).__name__),
                        error_message=str(e),
                        stack_trace=error_trace,
                        context=f"Processing AI message: {message}"
                    )
                    db.add(error_log)
                    db.commit()
            except Exception as db_error:
                print(f"Failed to log error to database: {db_error}")
        # Broadcast AI response to all users
        response_message = {
            "type": "chat_message",
            "sender": "AI Assistant",
            "message": ai_response if isinstance(ai_response, str) else str(ai_response),
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"Sending AI response: {response_message}")  
        for user_connections in connected_users.values():
            for ws in user_connections:
                try:
                    await ws.send_json(response_message)
                except Exception as e:
                    print(f"Error broadcasting message to user: {e}")
    except Exception as e:
        print(f"Unexpected error in send_ai_response: {e}")
    

@app.websocket("/ws/chat")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for real-time chat communication.
    
    This endpoint handles the WebSocket connection for the chat interface, including:
    - Authentication via JWT token
    - Connection management
    - Message routing
    - Error handling and logging
    """
    from app.websocket.chat_manager import manager as chat_manager
    from app.websocket.chat_endpoint import get_current_user_websocket
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    
    # Database session management
    db = None
    client_id = str(uuid.uuid4())
    user = None
    room_id = "general"
    
    try:
        db = SessionLocal()
        
        # Accept the WebSocket connection
        await websocket.accept()
        
        # First message should be authentication
        try:
            data = await websocket.receive_text()
            auth_data = json.loads(data)
            
            if auth_data.get('type') != 'auth' or not auth_data.get('token'):
                await websocket.send_json({
                    "type": "error",
                    "message": "Authentication required"
                })
                await websocket.close(code=4003)
                return
                
            # Authenticate user (WebSocket version)
            user = get_current_user_websocket(auth_data['token'], db)
            
            if user is None:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid authentication token"
                })
                await websocket.close(code=4003)
                return
            
        except json.JSONDecodeError:
            await websocket.send_json({
                "type": "error",
                "message": "Invalid authentication data"
            })
            await websocket.close(code=4003)
            return
        except HTTPException as e:
            await websocket.send_json({
                "type": "error",
                "message": str(e.detail) if hasattr(e, 'detail') else "Authentication failed"
            })
            await websocket.close(code=4003)
            return
        
        # Update user info with the one from the client
        user_info = {
            'username': auth_data.get('username', f'user-{user.id}'),
            'status': 'online',
            'last_seen': None
        }
        
        # Register the connection with the chat manager
        await chat_manager.connect(websocket, client_id, str(user.id), user_info['username'])
        
        # Join the default room
        await chat_manager.join_room(client_id, str(user.id), room_id)
        
        # Send welcome message
        await chat_manager.send_personal_message({
            "type": "connection_established",
            "message": f"Welcome to the chat, {user_info['username']}!",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user.id),
            "username": user_info['username']
        }, client_id)
        
        # Note: join_room() already broadcasts user_joined message, no need to duplicate
        
        # Main message loop
        while True:
            try:
                # Wait for any message from the client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Process different message types
                message_type = message_data.get("type")
                
                if not message_type:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Message type is required"
                    })
                    continue

                if message_type == "chat_message":
                    # Validate message content
                    content = message_data.get("content", "").strip()
                    if not content:
                        continue
                        
                    # Broadcast chat message to room
                    await chat_manager.broadcast({
                        "type": "chat_message",
                        "user_id": str(user.id),
                        "username": user_info['username'],
                        "room_id": room_id,
                        "content": content,
                        "timestamp": datetime.utcnow().isoformat()
                    }, room_id)
                    
                elif message_type == "typing":
                    # Broadcast typing indicator to room (except sender)
                    is_typing = bool(message_data.get("is_typing", False))
                    await chat_manager.broadcast({
                        "type": "user_typing",
                        "user_id": str(user.id),
                        "username": user_info['username'],
                        "room_id": room_id,
                        "is_typing": is_typing,
                        "timestamp": datetime.utcnow().isoformat()
                    }, room_id, exclude=[client_id])
                    
                elif message_type == "ping":
                    # Respond to ping with pong to keep connection alive
                    logger.info(f"Received ping from client {client_id}, sending pong...")
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    logger.info(f"Pong sent to client {client_id}")
                    
                elif message_type == "join_room":
                    # Switch to a different room
                    new_room_id = message_data.get("room_id")
                    if new_room_id:
                        # Leave current room (NOT async)
                        chat_manager.leave_room(client_id, str(user.id), room_id)
                        
                        # Update room_id variable
                        room_id = new_room_id
                        
                        # Join new room
                        await chat_manager.join_room(client_id, str(user.id), room_id)
                        
                        logger.info(f"User {user.id} switched to room {room_id}")
                        
                        # Send confirmation
                        await chat_manager.send_personal_message({
                            "type": "room_joined",
                            "room_id": room_id,
                            "message": f"Joined room {room_id}",
                            "timestamp": datetime.utcnow().isoformat()
                        }, client_id)
                    
                elif message_type == "get_online_users":
                    # Get list of online users
                    online_users = []
                    for uid, info in chat_manager.user_info.items():
                        if uid in chat_manager.user_connections and chat_manager.user_connections[uid]:
                            online_users.append({
                                'user_id': uid,
                                'username': info['username'],
                                'status': info['status']
                            })
                    
                    await chat_manager.send_personal_message({
                        "type": "online_users",
                        "users": online_users,
                        "timestamp": datetime.utcnow().isoformat()
                    }, client_id)
                    
            except WebSocketDisconnect:
                # Client disconnected normally, break the loop
                logger.info(f"Client {client_id} disconnected normally")
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except RuntimeError as e:
                # WebSocket has been disconnected, break the loop
                if "disconnect message has been received" in str(e):
                    logger.info(f"WebSocket already disconnected: {client_id}")
                    break
                else:
                    raise  # Re-raise if it's a different RuntimeError
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}", exc_info=True)
                try:
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e) if str(e) else "An error occurred while processing your message"
                    })
                except:
                    pass  # Client may have disconnected
                    break  # Exit loop if we can't send error message
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id} (User: {user.id if user else 'unknown'})")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
    finally:
        # Clean up database session
        if db:
            db.close()
        
        # Clean up on disconnect
        if user:
            try:
                # Remove connection FIRST (before broadcasting)
                await chat_manager.disconnect(client_id, str(user.id))
                
                # Notify room about user leaving (excluding the disconnected client)
                await chat_manager.broadcast({
                    "type": "user_left",
                    "user_id": str(user.id),
                    "username": user.username,
                    "room_id": room_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": f"{user.username} has left the chat"
                }, room_id, exclude=[client_id])
            except Exception as e:
                logger.error(f"Error during WebSocket cleanup: {str(e)}", exc_info=True)

# Test endpoint for debugging chat page
@app.get("/test-chat", response_class=HTMLResponse)
async def test_chat_page(request: Request):
    """Simple test page to verify chat UI is working."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Chat</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            #chat-messages { 
                height: 400px; 
                border: 1px solid #ccc; 
                padding: 10px; 
                margin-bottom: 10px;
                overflow-y: auto;
            }
            .message { margin: 5px 0; padding: 5px; border-bottom: 1px solid #eee; }
            .user-message { text-align: right; color: blue; }
            .bot-message { text-align: left; color: green; }
        </style>
    </head>
    <body>
        <h1>Test Chat</h1>
        <div id="chat-messages">
            <div class="message bot-message">System: Welcome to the test chat!</div>
        </div>
        <form id="message-form" onsubmit="sendMessage(event)">
            <input type="text" id="message-input" placeholder="Type a message..." style="width: 80%; padding: 8px;">
            <button type="submit" style="padding: 8px 15px;">Send</button>
        </form>
        
        <script>
            function addMessage(sender, message, isUser = false) {
                const messages = document.getElementById('chat-messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
                messageDiv.textContent = `${sender}: ${message}`;
                messages.appendChild(messageDiv);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function sendMessage(event) {
                event.preventDefault();
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                
                if (message) {
                    addMessage('You', message, true);
                    input.value = '';
                    
                    // Simulate bot response
                    setTimeout(() => {
                        addMessage('Bot', `You said: ${message}`);
                    }, 500);
                }
            }
            
            // Focus the input field on page load
            document.addEventListener('DOMContentLoaded', () => {
                document.getElementById('message-input').focus();
            });
        </script>
    </body>
    </html>
    """

# Root endpoint
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from fastapi import HTTPException
from datetime import datetime, timedelta

# Templates
templates = Jinja2Templates(directory="templates")

@app.get("/test")
async def test_page(request: Request):
    """Test page to verify template rendering."""
    return templates.TemplateResponse("test.html", {"request": request})

@app.get("/")
async def root():
    """Redirect to the login page."""
    return RedirectResponse(url="/login")

@app.get("/login")
async def login_page(request: Request):
    """Serve the login page with any error messages."""
    error = request.query_params.get("error", "")
    registered = request.query_params.get("registered", "")
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": error, "registered": registered}
    )

@app.get("/register")
async def register_page(request: Request):
    """Serve the registration page with any error messages."""
    error = request.query_params.get("error", "")
    return templates.TemplateResponse(
        "register.html", 
        {
            "request": request,
            "error": error.replace("+", " ") if error else None
        }
    )

@app.get("/rooms")
async def rooms_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Serve the private rooms page.
    Requires authentication - redirects to /login if not authenticated.
    
    OBSERVABILITY: Logs page access attempts
    """
    print("\n[TRACE] ====== ROOMS PAGE REQUEST ======")
    print(f"[TRACE] Request URL: {request.url}")
    
    try:
        # Get token from cookies or URL
        token = request.query_params.get("token") or request.cookies.get("access_token")
        
        if not token:
            print("[EVAL] rooms_page: no token, redirecting to login")
            return RedirectResponse(url="/login?error=Please+log+in+first")
        
        # Verify token and get user
        from app.auth import SECRET_KEY, ALGORITHM
        from jose import JWTError, jwt
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            
            if not username:
                print("[EVAL] rooms_page: invalid token, no username")
                return RedirectResponse(url="/login?error=Invalid+session")
            
            # Get user from database
            from datamanager.data_manager import DataManager
            dm = DataManager("data.sqlite.db")
            user = dm.get_user_by_username(username)
            
            if not user:
                print(f"[EVAL] rooms_page: user {username} not found")
                return RedirectResponse(url="/login?error=User+not+found")
            
            print(f"[TRACE] rooms_page: authenticated user {username} (ID: {user.id})")
            
            # Serve the rooms page
            return templates.TemplateResponse(
                "rooms.html",
                {
                    "request": request,
                    "username": user.username,
                    "user_id": user.id,
                    "access_token": token
                }
            )
            
        except JWTError as e:
            print(f"[ERROR] rooms_page: JWT error - {e}")
            return RedirectResponse(url="/login?error=Session+expired")
            
    except Exception as e:
        print(f"[ERROR] rooms_page: exception - {e}")
        return RedirectResponse(url="/login?error=An+error+occurred")


@app.get("/chat")
async def chat_page(
    request: Request, 
    db: Session = Depends(get_db)
):
    """
    Serve the chat page with the new template.
    This endpoint requires authentication and will redirect to /login if not authenticated.
    """
    print("\n[DEBUG] ====== CHAT PAGE REQUEST ======")
    print(f"[DEBUG] Request URL: {request.url}")
    print(f"[DEBUG] Cookies: {request.cookies}")
    
    try:
        # Try to get token from URL first
        token = request.query_params.get("token")
        token_source = "URL"
        
        # If no token in URL, try to get it from cookies
        if not token:
            print("[DEBUG] No token in URL, checking cookies...")
            token = request.cookies.get("access_token") or request.cookies.get("token")
            token_source = "cookie"
            
            # If token is in Bearer format, extract it
            if token and token.startswith("Bearer "):
                print("[DEBUG] Found Bearer token, extracting...")
                token = token[7:]  # Remove 'Bearer ' prefix
        
        # Check if token exists
        if not token:
            print("[ERROR] No token found in request")
            print(f"[DEBUG] All cookies: {request.cookies}")
            return RedirectResponse(url="/login")
            
        print(f"[DEBUG] Token found in {token_source}")
        print(f"[DEBUG] Token length: {len(token) if token else 0} characters")
            
        try:
            print("[DEBUG] Attempting to verify token...")
            # Verify the token
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM],
                options={"verify_exp": True}
            )
            
            username: str = payload.get("sub")
            if not username:
                print("[ERROR] No username in token payload")
                print(f"[DEBUG] Token payload: {payload}")
                raise HTTPException(status_code=400, detail="Invalid token")
                
            print(f"[DEBUG] Successfully authenticated as user: {username}")
            
            # Get user from database
            print(f"[DEBUG] Fetching user from database: {username}")
            user = db.query(User).filter(User.username == username).first()
            if not user:
                print(f"[ERROR] User not found in database: {username}")
                raise HTTPException(status_code=404, detail="User not found")
                
            # Prepare user data for the template
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": getattr(user, 'email', ''),
                "is_active": user.is_active,
                "role": getattr(user, 'role', 'user'),
                "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
            }
            
            print(f"[DEBUG] User data prepared: {user_data}")
            
            # Generate a unique client ID for this session
            import uuid
            client_id = str(uuid.uuid4())
            
            # Create WebSocket URL
            ws_scheme = 'wss' if request.url.scheme == 'https' else 'ws'
            ws_url = f"{ws_scheme}://{request.url.hostname}:{request.url.port}/ws/chat"
            
            # Create response with the new chat template
            response = templates.TemplateResponse(
                "new-chat.html", 
                {
                    "request": request,
                    "current_user": user_data,
                    "ws_url": ws_url,
                    "access_token": token,  # Pass the token to the template
                    "token": token  # Also pass as 'token' for backward compatibility
                }
            )
            
            # Refresh the token to extend session
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            new_token = create_access_token(
                data={"sub": user.username},
                expires_delta=access_token_expires
            )
            
            # Set the new token in the cookie
            response.set_cookie(
                key="access_token",
                value=f"Bearer {new_token}",
                httponly=True,
                max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                samesite='lax',
                secure=request.url.scheme == 'https'
            )
            
            return response
            
        except JWTError as e:
            print(f"[CHAT] Token validation failed: {str(e)}")
            response = RedirectResponse(url="/login")
            response.delete_cookie("access_token")
            return response
            
    except HTTPException as e:
        print(f"[CHAT] HTTP Error: {str(e)}")
        return RedirectResponse(url=f"/login?error={str(e.detail)}")
        
    except Exception as e:
        print(f"[CHAT] Error in chat_page: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# UserCreate model is defined above with proper configuration

@app.post("/api/auth/login")
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login a user and return a JWT token in a cookie.
    
    Handles both JSON and form-encoded requests.
    Returns:
    - JSON response with token for API requests
    - Redirect with cookies for form submissions
    """
    content_type = request.headers.get('content-type', '')
    is_json = 'application/json' in content_type or content_type.startswith('application/json')
    
    try:
        # Parse request data
        if is_json and not request.headers.get('content-type', '').startswith('multipart/form-data'):
            try:
                data = await request.json()
                username = data.get('username')
                password = data.get('password')
            except json.JSONDecodeError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Invalid JSON format"}
                )
        else:
            form_data = await request.form()
            username = form_data.get('username')
            password = form_data.get('password')
        
        print(f"[DEBUG] Login attempt for user: {username}")
        
        # Validate input
        if not username or not password:
            error_msg = "Username and password are required"
            print(f"[DEBUG] {error_msg}")
            if is_json:
                return JSONResponse(
                    status_code=400,
                    content={"detail": error_msg}
                )
            return RedirectResponse(
                url=f"/login?error={error_msg.replace(' ', '+')}",
                status_code=303
            )
        
        # Authenticate user
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            error_msg = "Incorrect username or password"
            print(f"[DEBUG] {error_msg} for user: {username}")
            if is_json:
                return JSONResponse(
                    status_code=401,
                    content={"detail": error_msg}
                )
            return RedirectResponse(
                url=f"/login?error={error_msg.replace(' ', '+')}",
                status_code=303
            )
        
        # Create access token with 1-hour expiration
        access_token_expires = timedelta(minutes=60)  # 1 hour expiration
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=access_token_expires
        )
        
        # For development, use secure=False. In production, set to True and use HTTPS
        secure_cookie = False  # Change to True in production with HTTPS
        
        # Prepare response based on content type
        if is_json:
            response_data = {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "username": user.username,
                    "email": user.email
                }
            }
            response = JSONResponse(content=response_data)
        else:
            # For form submission, create a redirect response
            response = RedirectResponse(
                url="/chat",
                status_code=303
            )
        
        # Get the domain from the request (remove port if present)
        domain = request.url.hostname
        if ':' in domain:
            domain = domain.split(':')[0]
            
        # Set the access token cookie (HTTP-only for security)
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=3600,  # 1 hour in seconds
            secure=secure_cookie,
            samesite="lax",
            path="/",
            domain=domain if domain and domain != 'localhost' else None  # Don't set domain for localhost
        )
        
        # Set username in a cookie for the frontend
        response.set_cookie(
            key="username",
            value=user.username,
            max_age=3600,
            secure=secure_cookie,
            samesite="lax",
            path="/"
        )
        
        # Set a simple logged_in flag for the frontend to check
        response.set_cookie(
            key="logged_in",
            value="true",
            max_age=3600,
            secure=secure_cookie,
            samesite="lax",
            path="/"
        )
        
        # For debugging - set a non-httpOnly cookie as well
        response.set_cookie(
            key="auth_debug",
            value=f"user_{user.username}",
            max_age=3600,
            secure=secure_cookie,
            samesite="lax",
            path="/"
        )
        
        # For form submissions, we need to return the response directly
        if not is_json:
            return response
        
        print(f"[DEBUG] Login successful for user: {username}")
        return response
        
    except Exception as e:
        error_msg = f"An error occurred during login: {str(e)}"
        print(f"[ERROR] {error_msg}")
        if is_json:
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        return RedirectResponse(
            url="/login?error=An+error+occurred+during+login",
            status_code=303
        )

@app.post("/api/auth/register")
async def register_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        # Parse form data
        form_data = await request.form()
        username = form_data.get('username')
        email = form_data.get('email')
        password = form_data.get('password')
        confirm_password = form_data.get('confirm_password')
        
        # Validate required fields
        if not all([username, email, password, confirm_password]):
            return RedirectResponse(
                url="/register?error=All+fields+are+required",
                status_code=303
            )
            
        # Check if passwords match
        if password != confirm_password:
            return RedirectResponse(
                url="/register?error=Passwords+do+not+match",
                status_code=303
            )
        
        # Check if username already exists
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            return RedirectResponse(
                url="/register?error=Username+already+registered",
                status_code=303
            )
        
        # Check if email already exists
        db_email = db.query(User).filter(User.hashed_email == email).first()
        if db_email:
            return RedirectResponse(
                url="/register?error=Email+already+registered",
                status_code=303
            )
        
        # Hash the password
        hashed_password = pwd_context.hash(password)
        
        # Create new user
        db_user = User(
            username=username,
            hashed_email=email,
            hashed_password=hashed_password
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Redirect to login with success message
        return RedirectResponse(
            url="/login?registered=1",
            status_code=303
        )
        
    except Exception as e:
        db.rollback()
        return RedirectResponse(
            url=f"/register?error={str(e).replace(' ', '+')}",
            status_code=303
        )

# AI Chat endpoint
class AIChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class AIChatResponse(BaseModel):
    response: str
    thread_id: str
    tools_used: List[str] = []
    error: Optional[str] = None

@app.post("/api/ai-chat", response_model=AIChatResponse)
async def ai_chat(
    request: AIChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Process a message through the AI agent.
    
    - Triggered by /ai prefix or AI button in chat
    - Returns AI Social Coach response with context awareness
    - Supports translation, social behavior training, and memory
    """
    try:
        result = await ai_manager.get_response(
            user_id=current_user.id,
            message=request.message,
            thread_id=request.thread_id
        )
        
        return AIChatResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in AI chat endpoint: {str(e)}", exc_info=True)
        return AIChatResponse(
            response=f"I'm sorry, I encountered an error: {str(e)}",
            thread_id=request.thread_id or str(current_user.id),
            tools_used=[],
            error=str(e)
        )

# AI Chat Test Page
@app.get("/test-ai", response_class=HTMLResponse)
async def test_ai_page():
    """Serve the AI chat test page."""
    test_file = Path(__file__).parent.parent / "test_ai_browser.html"
    if test_file.exists():
        return test_file.read_text()
    return "<h1>Test file not found</h1>"

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "ok"}

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    # Any initialization code can go here
    pass

# For development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
