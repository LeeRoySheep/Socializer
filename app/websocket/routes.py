"""WebSocket routes for real-time communication."""
import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Set

from fastapi import (
    WebSocket, 
    WebSocketDisconnect, 
    status, 
    HTTPException,
    Depends
)
from fastapi.routing import APIRouter
from fastapi.websockets import WebSocketState
from jose import jwt

# Import JWT settings from config
from app.config import SECRET_KEY, ALGORITHM
from .connection_manager import ConnectionManager, manager

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

# For testing purposes, we'll use a simple user mapping
TEST_USERS = {
    'user1': {'username': 'Alice', 'is_active': True},
    'user2': {'username': 'Bob', 'is_active': True},
    'user3': {'username': 'Charlie', 'is_active': True}
}

async def get_user_info(token: str) -> Dict[str, Any]:
    """Get user information from JWT token.
    
    Args:
        token: JWT token from the client
        
    Returns:
        Dict containing user information if token is valid
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # In a real app, you would fetch the user from the database
        # For now, we'll use our test users
        user = TEST_USERS.get(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
            
        return {
            "user_id": username,
            "username": user["username"],
            "is_active": user["is_active"]
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.JWTError, jwt.JWTClaimsError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.websocket("/ws/chat/{room_id}")
async def websocket_chat_endpoint(
    websocket: WebSocket, 
    room_id: str,
    token: str = None
):
    """WebSocket endpoint for chat functionality.
    
    Handles:
    - Authentication
    - Connection management
    - Message routing
    - Online user tracking
    
    Args:
        websocket: The WebSocket connection
        room_id: The chat room ID
        token: JWT token for authentication (can be in query params or first message)
    """
    # Accept the WebSocket connection first
    await websocket.accept()
    
    client_id = str(uuid.uuid4())
    user_info = None
    
    try:
        # Try to get token from query parameters first
        if not token:
            # If no token in query params, expect it in the first message
            try:
                first_message = await websocket.receive_text()
                message_data = json.loads(first_message)
                if message_data.get('type') == 'auth' and 'token' in message_data:
                    token = message_data['token']
                else:
                    logger.warning(f"Client {client_id} did not provide a valid auth token")
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
                    return
            except (WebSocketDisconnect, json.JSONDecodeError) as e:
                logger.warning(f"Client {client_id} disconnected during authentication: {e}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication")
                return
        
        # Validate the token
        try:
            user_info = await get_user_info(token)
            if not user_info or not user_info.get('is_active', True):
                logger.warning(f"Client {client_id} provided invalid or inactive user token")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or inactive user")
                return
        except Exception as e:
            logger.error(f"Error validating token for client {client_id}: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return
        
        # Add the connection to the manager
        if not await manager.connect(websocket, client_id, user_info['user_id']):
            logger.error(f"Failed to add connection {client_id} to manager")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Server error")
            return
        
        logger.info(f"New WebSocket connection: {client_id} (User: {user_info['user_id']}, Room: {room_id})")
        
        # Send welcome message
        welcome_msg = {
            "type": "system",
            "message": f'Welcome to the chat, {user_info["username"]}!',
            "timestamp": datetime.utcnow().isoformat(),
            "room_id": room_id
        }
        await manager.send_personal_message(json.dumps(welcome_msg), websocket)
        
        # Notify others that this user has joined
        join_notification = {
            "type": "user_joined",
            "user_id": user_info['user_id'],
            "username": user_info['username'],
            "timestamp": datetime.utcnow().isoformat(),
            "room_id": room_id
        }
        await manager.broadcast(
            json.dumps(join_notification),
            skip_connections={websocket}  # Don't send to self
        )
        
        # Main message loop
        while True:
            try:
                # Receive message with timeout to detect disconnections
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300)  # 5 min timeout
                
                # Process the message
                await handle_client_message(websocket, client_id, user_info['user_id'], data, room_id)
                
            except asyncio.TimeoutError:
                # Send ping to check if client is still alive
                try:
                    ping_msg = json.dumps({
                        "type": "ping",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    await manager.send_personal_message(ping_msg, websocket)
                    continue
                except Exception as ping_error:
                    logger.info(f"Ping failed for {client_id}, assuming disconnection: {ping_error}")
                    break
                    
            except WebSocketDisconnect:
                logger.info(f"Client {client_id} disconnected")
                break
                
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket endpoint for {client_id}: {e}", exc_info=True)
        
    finally:
        # Clean up connection
        if user_info:
            # Notify others that this user has left
            leave_notification = {
                "type": "user_left",
                "user_id": user_info['user_id'],
                "username": user_info['username'],
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id
            }
            
            try:
                await manager.broadcast(
                    json.dumps(leave_notification),
                    skip_connections={websocket}
                )
            except Exception as broadcast_error:
                logger.error(f"Error sending leave notification: {broadcast_error}")
            
            # Disconnect the user
            await manager.disconnect(client_id, user_info['user_id'])
            
        logger.info(f"Connection closed: {client_id} (User: {user_info['user_id'] if user_info else 'unknown'}, Room: {room_id})")
    """WebSocket endpoint for chat functionality.
    
    Handles:
    - Authentication
    - Connection management
    - Message routing
    - Online user tracking
    
    Args:
        websocket: The WebSocket connection
        room_id: The chat room ID
        token: Optional JWT token for authentication
    """
    # Generate a unique client ID for this connection
    client_id = str(uuid.uuid4())
    user_info = None
    
    try:
        # Authenticate the user before accepting the connection
        if not token:
            logger.warning(f"Connection {client_id} rejected: No token provided")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
            return
            
        try:
            # Validate the token and get user info
            user_info = await get_user_info(token)
            if not user_info or not user_info.get('is_active', True):
                logger.warning(f"Connection {client_id} rejected: Invalid or inactive user")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or inactive user")
                return
        except HTTPException as e:
            logger.warning(f"Authentication failed for {client_id}: {e.detail}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(e.detail))
            return
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}", exc_info=True)
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication error")
            return
        
        # Add the connection to the manager
        if not await manager.connect(websocket, client_id, user_info['user_id']):
            logger.error(f"Failed to add connection {client_id} to manager")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Server error")
            return
        
        logger.info(f"New WebSocket connection established: {client_id} (User: {user_info['user_id']})")
        
        try:
            # Send welcome message
            welcome_msg = {
                "type": "system",
                "message": f'Welcome to the chat, {user_info["user_id"]}!',
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id
            }
            await manager.send_personal_message(json.dumps(welcome_msg), websocket)
            
            # Notify others that this user has joined
            join_notification = {
                "type": "user_joined",
                "user_id": user_info['user_id'],
                "username": user_info['user_id'],  # Using user_id as username for now
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id
            }
            await manager.broadcast(
                json.dumps(join_notification),
                skip_connections={websocket}  # Don't send to self
            )
            
            # Main message loop
            while True:
                try:
                    # Receive message with timeout to detect disconnections
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=300  # 5 minute timeout
                    )
                    
                    # Process the message
                    await handle_client_message(websocket, client_id, user_info['user_id'], data, room_id)
                    
                except asyncio.TimeoutError:
                    # Send ping to check if client is still alive
                    try:
                        ping_msg = json.dumps({
                            "type": "ping",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        await manager.send_personal_message(ping_msg, websocket)
                        continue
                    except Exception as ping_error:
                        logger.info(f"Ping failed for {client_id}, assuming disconnection: {ping_error}")
                        break
                        
                except WebSocketDisconnect:
                    logger.info(f"Client {client_id} disconnected")
                    break
                    
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}", exc_info=True)
                    error_msg = {
                        "type": "error",
                        "message": "Error processing message",
                        "timestamp": datetime.utcnow().isoformat(),
                        "error": str(e)
                    }
                    try:
                        await manager.send_personal_message(json.dumps(error_msg), websocket)
                    except Exception as send_error:
                        logger.error(f"Failed to send error to {client_id}: {send_error}")
                        break  # Connection is likely dead
        
        except Exception as e:
            logger.error(f"Unexpected error in message loop for {client_id}: {e}", exc_info=True)
            
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket endpoint: {e}", exc_info=True)
        
    finally:
        try:
            # Clean up connection
            if user_info:
                # Notify others that this user has left
                leave_notification = {
                    "type": "user_left",
                    "user_id": user_info['user_id'],
                    "username": user_info['user_id'],
                    "timestamp": datetime.utcnow().isoformat(),
                    "room_id": room_id
                }
                
                # Send notification before disconnecting
                try:
                    await manager.broadcast(
                        json.dumps(leave_notification),
                        skip_connections={websocket}  # Don't send to self
                    )
                except Exception as broadcast_error:
                    logger.error(f"Error sending leave notification: {broadcast_error}")
                
                # Disconnect the user
                await manager.disconnect(client_id, user_info['user_id'])
                
            logger.info(f"Connection closed: {client_id} (User: {user_info['user_id'] if user_info else 'unknown'})")
            
        except Exception as cleanup_error:
            logger.error(f"Error during connection cleanup: {cleanup_error}", exc_info=True)

async def handle_client_message(
    websocket: WebSocket, 
    client_id: str, 
    user_id: str, 
    data: str,
    room_id: str
):
    """Handle incoming WebSocket messages.
    
    Args:
        websocket: The WebSocket connection
        client_id: The unique ID of the client connection
        user_id: The ID of the user sending the message
        data: The raw message data as a string (should be JSON)
        room_id: The chat room ID
    """
    try:
        # Parse the message data
        try:
            message = json.loads(data)
            message_type = message.get("type")
            
            if not message_type:
                raise ValueError("Message type is required")
                
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")
            
        # Handle different message types
        if message_type == "chat":
            # Handle chat message
            text = message.get("text", "")
            if not text.strip():
                raise ValueError("Message text cannot be empty")
                
            # Broadcast the message to all connected clients in the room
            chat_message = {
                "type": "chat",
                "from": user_id,
                "text": text,
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id
            }
            
            await manager.broadcast(
                json.dumps(chat_message),
                room_id=room_id
            )
            
        elif message_type == "typing":
            # Handle typing indicator
            is_typing = message.get("is_typing", False)
            
            typing_msg = {
                "type": "typing",
                "user_id": user_id,
                "is_typing": is_typing,
                "timestamp": datetime.utcnow().isoformat(),
                "room_id": room_id
            }
            
            # Broadcast to all except the sender
            await manager.broadcast(
                json.dumps(typing_msg),
                room_id=room_id,
                skip_connections={websocket}
            )
            
        elif message_type == "get_online_users":
            # Handle request for online users
            await send_online_users(websocket, room_id, message.get("request_id"))
            
        elif message_type == "ping":
            # Handle ping (keep-alive)
            pong_msg = {
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.send_personal_message(json.dumps(pong_msg), websocket)
            
        else:
            raise ValueError(f"Unknown message type: {message_type}")
            
    except Exception as e:
        logger.error(f"Error handling client message: {e}", exc_info=True)
        error_msg = {
            "type": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
        await manager.send_personal_message(json.dumps(error_msg), websocket)

async def send_online_users(
    websocket: WebSocket, 
    room_id: str, 
    request_id: str = None
) -> None:
    """Send the list of online users to the client.
    
    Args:
        websocket: The WebSocket connection to send the list to
        room_id: The chat room ID
        request_id: Optional request ID for matching requests with responses
    """
    try:
        # Get online users from the connection manager
        online_users = []
        
        # Get a snapshot of user connections to avoid modification during iteration
        user_connections_snapshot = {}
        async with manager._lock:
            user_connections_snapshot = manager.user_connections.copy()
        
        # Process each user's connections
        for user_id, connections in user_connections_snapshot.items():
            # Get active connections for this user
            active_connections = [
                conn for conn in connections 
                if conn.client_state == WebSocketState.CONNECTED
            ]
            
            if active_connections:
                # Get the most recent activity time from all connections
                last_active = 0
                for conn in active_connections:
                    for client_id, active_conn in manager.active_connections.items():
                        if active_conn == conn and client_id in manager.connection_info:
                            conn_info = manager.connection_info[client_id]
                            last_active = max(last_active, conn_info.get('last_active', 0))
                            break
                
                # Add user to online list
                online_users.append({
                    'user_id': user_id,
                    'username': user_id,  # Using user_id as username for now
                    'status': 'online',
                    'last_active': datetime.fromtimestamp(last_active).isoformat() if last_active > 0 else None,
                    'connection_count': len(active_connections)
                })
        
        # Sort users by username (or user_id) for consistent ordering
        online_users.sort(key=lambda u: u['username'].lower())
        
        # Prepare the response
        response = {
            'type': 'online_users',
            'users': online_users,
            'count': len(online_users),
            'timestamp': datetime.utcnow().isoformat(),
            'room_id': room_id
        }
        
        # Add request_id if provided
        if request_id is not None:
            response['request_id'] = request_id
        
        logger.debug(f"Sending {len(online_users)} online users to client")
        
        # Send the response
        await manager.send_personal_message(json.dumps(response), websocket)
        
    except Exception as e:
        logger.error(f"Error in send_online_users: {e}", exc_info=True)
        error_response = {
            'type': 'error',
            'message': 'Failed to get online users',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }
        if request_id is not None:
            error_response['request_id'] = request_id
            
        try:
            await manager.send_personal_message(json.dumps(error_response), websocket)
        except Exception as send_error:
            logger.error(f"Failed to send error response: {send_error}")


# ==========================================
# PRIVATE ROOM WEBSOCKET
# ==========================================

from app.websocket.room_websocket import handle_room_websocket, room_manager
from datamanager.data_manager import DataManager

@router.websocket("/rooms/{room_id}")
async def websocket_room_endpoint(
    websocket: WebSocket,
    room_id: int
):
    """
    WebSocket endpoint for private room messaging.
    
    Connect to a room for real-time messaging:
    ws://localhost:8000/ws/rooms/123?token=YOUR_JWT_TOKEN
    
    Args:
        room_id: ID of the room to connect to
        token: JWT token (query parameter)
    """
    # Get token from query params
    token = websocket.query_params.get("token")
    
    logger.info(f"WebSocket connection attempt to room {room_id}")
    logger.info(f"Token present: {bool(token)}")
    
    if not token:
        logger.error("No token provided")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Authenticate user
    try:
        from app.auth import SECRET_KEY, ALGORITHM
        from jose import JWTError
        
        # Decode JWT token
        try:
            logger.info(f"Decoding token with key: {SECRET_KEY[:10]}...")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            logger.info(f"Token decoded successfully, user: {user_id}")
            
            if not user_id:
                logger.error("No user_id in token")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Get user from database
        dm = DataManager("data.sqlite.db")
        from datamanager.data_model import User
        
        # user_id from token is actually the username
        user = dm.get_user_by_username(user_id)
        
        if not user:
            logger.error(f"User {user_id} not found")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        logger.info(f"User authenticated: {user.username} (ID: {user.id})")
        
        # Handle the WebSocket connection
        await handle_room_websocket(websocket, room_id, user)
        
    except Exception as e:
        logger.error(f"Error in room WebSocket: {e}")
        import traceback
        traceback.print_exc()
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
