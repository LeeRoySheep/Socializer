"""
Private Chat Rooms API Router

REST API endpoints for managing private chat rooms, invites, and messages.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.auth import get_current_user
from datamanager.data_manager import DataManager
from datamanager.data_model import User, ChatRoom, RoomMember, RoomMessage, RoomInvite

router = APIRouter(prefix="/api/rooms", tags=["rooms"])


# ==========================================
# REQUEST/RESPONSE MODELS
# ==========================================

class RoomCreate(BaseModel):
    """Request model for creating a room."""
    name: Optional[str] = Field(None, description="Optional custom room name")
    invitees: List[int] = Field(default_factory=list, description="User IDs to invite")
    room_type: str = Field("group", description="Room type: 'direct' or 'group'")
    ai_enabled: bool = Field(True, description="Enable AI in this room")
    password: Optional[str] = Field(None, description="Optional password for room protection")


class RoomResponse(BaseModel):
    """Response model for room details."""
    id: int
    name: Optional[str]
    creator_id: int
    created_at: datetime
    is_active: bool
    room_type: str
    ai_enabled: bool
    member_count: int
    has_password: bool = False
    
    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    """Response model for room member."""
    id: int
    user_id: Optional[int]
    role: str
    joined_at: datetime
    username: Optional[str] = None
    is_ai: bool = False


class MessageCreate(BaseModel):
    """Request model for sending a message."""
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    """Response model for a room message."""
    id: int
    room_id: int
    sender_id: Optional[int]
    sender_type: str
    content: str
    message_type: str
    created_at: datetime
    sender_username: Optional[str] = None


class InviteResponse(BaseModel):
    """Response model for room invite."""
    id: int
    room_id: int
    room_name: Optional[str]
    inviter_id: int
    inviter_username: str
    invitee_id: int
    status: str
    created_at: datetime
    has_password: bool = False


class AcceptInviteRequest(BaseModel):
    """Request model for accepting invite."""
    password: Optional[str] = Field(None, description="Password if room is protected")


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_dm() -> DataManager:
    """Get DataManager instance."""
    return DataManager("data.sqlite.db")


def check_room_access(room_id: int, user_id: int, dm: DataManager) -> ChatRoom:
    """
    Verify user has access to room.
    
    Raises:
        HTTPException: If room not found or user not a member
    """
    room = dm.get_room(room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    if not dm.is_user_in_room(user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this room"
        )
    
    return room


# ==========================================
# ROOM MANAGEMENT ENDPOINTS
# ==========================================

@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new private chat room.
    
    - **name**: Optional custom name (auto-generated if not provided)
    - **invitees**: List of user IDs to invite
    - **room_type**: 'direct' for 1-on-1, 'group' for multiple users
    - **ai_enabled**: AI is ALWAYS enabled for moderation (monitoring empathy, cultural sensitivity, misunderstandings)
    """
    dm = get_dm()
    
    # IMPORTANT: AI is always enabled for all rooms to monitor:
    # - Misunderstandings between users
    # - Lack of empathy
    # - Cultural and social context
    # - Communication standards
    import sys
    print(f"[TRACE] create_room: AI moderation enforced (always enabled)", flush=True)
    sys.stdout.flush()
    
    # Create room
    room = dm.create_room(
        creator_id=current_user.id,
        name=room_data.name,
        room_type=room_data.room_type,
        ai_enabled=True,  # ALWAYS TRUE - AI is mandatory for moderation
        password=room_data.password
    )
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create room"
        )
    
    # Send invites
    for invitee_id in room_data.invitees:
        dm.invite_user_to_room(room.id, current_user.id, invitee_id)
    
    # Get member count
    members = dm.get_room_members(room.id)
    
    return RoomResponse(
        id=room.id,
        name=room.name,
        creator_id=room.creator_id,
        created_at=room.created_at,
        is_active=room.is_active,
        room_type=room.room_type,
        ai_enabled=room.ai_enabled,
        member_count=len(members),
        has_password=bool(room.password)
    )


@router.get("/", response_model=List[RoomResponse])
async def get_my_rooms(current_user: User = Depends(get_current_user)):
    """
    Get all rooms where current user is a member.
    
    Returns list of rooms with member counts.
    """
    dm = get_dm()
    rooms = dm.get_user_rooms(current_user.id)
    
    response = []
    for room in rooms:
        members = dm.get_room_members(room.id)
        response.append(RoomResponse(
            id=room.id,
            name=room.name,
            creator_id=room.creator_id,
            created_at=room.created_at,
            is_active=room.is_active,
            room_type=room.room_type,
            ai_enabled=room.ai_enabled,
            member_count=len(members),
            has_password=bool(room.password)
        ))
    
    return response


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific room.
    
    User must be a member to access room details.
    """
    dm = get_dm()
    room = check_room_access(room_id, current_user.id, dm)
    
    members = dm.get_room_members(room.id)
    
    return RoomResponse(
        id=room.id,
        name=room.name,
        creator_id=room.creator_id,
        created_at=room.created_at,
        is_active=room.is_active,
        room_type=room.room_type,
        ai_enabled=room.ai_enabled,
        member_count=len(members),
        has_password=bool(room.password)
    )


@router.delete("/{room_id}", status_code=status.HTTP_200_OK)
async def delete_room(
    room_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a room. Only the creator can delete.
    Soft deletes by marking as inactive.
    """
    dm = get_dm()
    
    with dm.get_session() as session:
        room = session.query(ChatRoom).filter(ChatRoom.id == room_id).first()
        
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        # Only creator can delete
        if room.creator_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the room creator can delete this room"
            )
        
        # Deactivate the room (soft delete)
        room.is_active = False
        session.commit()
        
        print(f"[TRACE] delete_room: room {room_id} deleted by user {current_user.id}", flush=True)
        
    return {"message": "Room deleted successfully"}


@router.post("/{room_id}/leave", status_code=status.HTTP_200_OK)
async def leave_room(
    room_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Leave a room.
    
    User will no longer see messages or have access to the room.
    """
    dm = get_dm()
    check_room_access(room_id, current_user.id, dm)
    
    success = dm.leave_room(current_user.id, room_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to leave room"
        )
    
    return {"message": "Successfully left the room"}


# ==========================================
# MEMBER MANAGEMENT ENDPOINTS
# ==========================================

@router.get("/{room_id}/members", response_model=List[MemberResponse])
async def get_room_members(
    room_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get all members of a room.
    
    Returns list of members including AI.
    """
    dm = get_dm()
    check_room_access(room_id, current_user.id, dm)
    
    members = dm.get_room_members(room_id)
    
    response = []
    for member in members:
        if member.user_id is None:
            # AI member
            response.append(MemberResponse(
                id=member.id,
                user_id=None,
                role=member.role,
                joined_at=member.joined_at,
                username="AI Assistant",
                is_ai=True
            ))
        else:
            # Regular user
            user = dm.get_user(member.user_id)
            response.append(MemberResponse(
                id=member.id,
                user_id=member.user_id,
                role=member.role,
                joined_at=member.joined_at,
                username=user.username if user else None,
                is_ai=False
            ))
    
    return response


# ==========================================
# INVITE MANAGEMENT ENDPOINTS
# ==========================================

class BatchInviteRequest(BaseModel):
    """Request model for batch inviting users."""
    user_ids: List[int] = Field(..., description="List of user IDs to invite")


@router.post("/{room_id}/invite", status_code=status.HTTP_201_CREATED)
async def invite_users_batch(
    room_id: int,
    invite_data: BatchInviteRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Invite multiple users to a room.
    
    User must be a member to invite others.
    """
    dm = get_dm()
    check_room_access(room_id, current_user.id, dm)
    
    invited_count = 0
    failed_users = []
    
    for user_id in invite_data.user_ids:
        try:
            # Check if invitee exists
            invitee = dm.get_user(user_id)
            if not invitee:
                failed_users.append({"user_id": user_id, "reason": "User not found"})
                continue
            
            # Check if already a member
            if dm.is_user_in_room(user_id, room_id):
                failed_users.append({"user_id": user_id, "reason": "Already a member"})
                continue
            
            # Send invite
            invite = dm.invite_user_to_room(room_id, current_user.id, user_id)
            
            if invite:
                invited_count += 1
            else:
                failed_users.append({"user_id": user_id, "reason": "Failed to create invite"})
        except Exception as e:
            failed_users.append({"user_id": user_id, "reason": str(e)})
    
    return {
        "message": f"Invited {invited_count} user(s) successfully",
        "invited_count": invited_count,
        "failed": failed_users
    }


@router.post("/{room_id}/invite/{user_id}", status_code=status.HTTP_201_CREATED)
async def invite_user(
    room_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Invite a single user to a room.
    
    User must be a member to invite others.
    """
    dm = get_dm()
    check_room_access(room_id, current_user.id, dm)
    
    # Check if invitee exists
    invitee = dm.get_user(user_id)
    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a member
    if dm.is_user_in_room(user_id, room_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this room"
        )
    
    invite = dm.invite_user_to_room(room_id, current_user.id, user_id)
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invite"
        )
    
    return {"message": "Invite sent successfully", "invite_id": invite.id}


@router.get("/invites/pending", response_model=List[InviteResponse])
async def get_pending_invites(current_user: User = Depends(get_current_user)):
    """
    Get all pending room invites for current user.
    
    These should be displayed in the main chat with Accept/Decline buttons.
    """
    dm = get_dm()
    invites = dm.get_pending_invites(current_user.id)
    
    response = []
    for invite in invites:
        room = dm.get_room(invite.room_id)
        inviter = dm.get_user(invite.inviter_id)
        
        response.append(InviteResponse(
            id=invite.id,
            room_id=invite.room_id,
            room_name=room.name if room else None,
            inviter_id=invite.inviter_id,
            inviter_username=inviter.username if inviter else "Unknown",
            invitee_id=invite.invitee_id,
            status=invite.status,
            created_at=invite.created_at,
            has_password=bool(room.password) if room else False
        ))
    
    return response


@router.post("/invites/{invite_id}/accept", status_code=status.HTTP_200_OK)
async def accept_invite(
    invite_id: int,
    invite_data: Optional[AcceptInviteRequest] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Accept a room invite.
    
    IMPORTANT: Invited users do NOT need to provide password.
    Password protection only applies to uninvited users trying to join directly.
    User will be added as a member and can start chatting.
    """
    dm = get_dm()
    password = invite_data.password if invite_data else None
    success = dm.accept_invite(invite_id, current_user.id, password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to accept invite. Invite may be invalid or already processed."
        )
    
    return {"message": "Invite accepted successfully"}


@router.post("/invites/{invite_id}/decline", status_code=status.HTTP_200_OK)
async def decline_invite(
    invite_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Decline a room invite.
    
    Invite will be marked as declined.
    """
    dm = get_dm()
    success = dm.decline_invite(invite_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decline invite. Invite may not exist or already processed."
        )
    
    return {"message": "Invite declined"}


# ==========================================
# MESSAGE ENDPOINTS
# ==========================================

@router.get("/{room_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    room_id: int,
    limit: int = 50,
    before_id: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Get messages from a room.
    
    - **limit**: Maximum number of messages (default: 50)
    - **before_id**: Get messages before this message ID (for pagination)
    """
    dm = get_dm()
    check_room_access(room_id, current_user.id, dm)
    
    messages = dm.get_room_messages(room_id, limit, before_id)
    
    response = []
    for msg in messages:
        sender_username = None
        if msg.sender_id:
            sender = dm.get_user(msg.sender_id)
            sender_username = sender.username if sender else None
        elif msg.sender_type == "ai":
            sender_username = "AI Assistant"
        
        response.append(MessageResponse(
            id=msg.id,
            room_id=msg.room_id,
            sender_id=msg.sender_id,
            sender_type=msg.sender_type,
            content=msg.content,
            message_type=msg.message_type,
            created_at=msg.created_at,
            sender_username=sender_username
        ))
    
    return response


@router.post("/{room_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    room_id: int,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to a room.
    
    If AI is enabled, it will process and respond.
    """
    dm = get_dm()
    room = check_room_access(room_id, current_user.id, dm)
    
    # Add user message
    message = dm.add_room_message(
        room_id=room_id,
        sender_id=current_user.id,
        content=message_data.content,
        sender_type="user",
        message_type="text"
    )
    
    if not message:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )
    
    # TODO: Trigger AI response if ai_enabled
    # This will be implemented in Phase A.4
    
    return MessageResponse(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        sender_type=message.sender_type,
        content=message.content,
        message_type=message.message_type,
        created_at=message.created_at,
        sender_username=current_user.username
    )
