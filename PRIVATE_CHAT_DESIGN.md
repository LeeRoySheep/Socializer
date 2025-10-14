# 🏗️ Private Chat System Design

**Date:** 2025-10-14  
**Status:** Design Phase  
**Purpose:** Add private group chat with AI support

---

## 📋 Requirements Summary

### **Core Features:**
1. **Group Chat** - Multiple users in one room (including 1-on-1)
2. **Invite System** - Send invites as messages with accept/decline buttons
3. **AI Included** - AI participates in all private rooms
4. **Purpose** - Help users be empathetic and track social contacts

---

## 🗄️ Database Schema Design

### **1. ChatRoom Table**
Stores information about each private chat room.

```python
class ChatRoom(Base):
    """
    Private chat room that can contain multiple users + AI.
    """
    __tablename__ = "chat_rooms"
    
    id: int (PK)
    name: str                    # Room name (optional, can be auto-generated)
    creator_id: int (FK → users) # User who created the room
    created_at: datetime
    is_active: bool              # Room can be archived
    room_type: str               # 'private', 'group', 'direct' (1-on-1)
    ai_enabled: bool             # AI participation (default True)
    
    # Relationships
    members → RoomMember[]
    messages → RoomMessage[]
    invites → RoomInvite[]
```

### **2. RoomMember Table**
Tracks which users are members of which rooms.

```python
class RoomMember(Base):
    """
    Association table for users in chat rooms.
    """
    __tablename__ = "room_members"
    
    id: int (PK)
    room_id: int (FK → chat_rooms)
    user_id: int (FK → users)
    joined_at: datetime
    role: str                    # 'creator', 'member', 'ai'
    is_active: bool              # Member can leave room
    last_read_at: datetime       # For unread messages
    
    # Unique constraint: user can only be in room once
    __table_args__ = (UniqueConstraint('room_id', 'user_id'),)
```

### **3. RoomMessage Table**
Stores all messages in private rooms.

```python
class RoomMessage(Base):
    """
    Messages sent in private chat rooms.
    """
    __tablename__ = "room_messages"
    
    id: int (PK)
    room_id: int (FK → chat_rooms)
    sender_id: int (FK → users, nullable)  # NULL for AI
    sender_type: str             # 'user', 'ai'
    content: str                 # Message text
    message_type: str            # 'text', 'invite', 'system'
    metadata: JSON               # For invite buttons, etc.
    created_at: datetime
    edited_at: datetime (nullable)
    is_deleted: bool
```

### **4. RoomInvite Table**
Tracks pending and responded invites.

```python
class RoomInvite(Base):
    """
    Invitations to join private chat rooms.
    """
    __tablename__ = "room_invites"
    
    id: int (PK)
    room_id: int (FK → chat_rooms)
    inviter_id: int (FK → users)  # Who sent the invite
    invitee_id: int (FK → users)  # Who is being invited
    status: str                   # 'pending', 'accepted', 'declined'
    message_id: int (FK → room_messages)  # Reference to invite message
    created_at: datetime
    responded_at: datetime (nullable)
    
    # Unique constraint: can't invite same user twice to same room
    __table_args__ = (UniqueConstraint('room_id', 'invitee_id'),)
```

---

## 🔄 Workflow Design

### **Flow 1: Create Private Room**

```
User A wants to chat with User B

1. User A → POST /api/rooms/create
   Body: {
     "name": "Chat with Bob",
     "invitees": [user_b_id],
     "ai_enabled": true
   }

2. Backend creates:
   - ChatRoom (creator=User A)
   - RoomMember (User A as creator)
   - RoomInvite (for User B, status=pending)
   - RoomMessage (type=invite, shown in User B's chat)

3. User B sees invite message in their main chat:
   "User A invited you to 'Chat with Bob'"
   [Accept] [Decline]

4. User B clicks [Accept]:
   - RoomInvite status → 'accepted'
   - Create RoomMember (User B)
   - User B can now access room
```

### **Flow 2: Send Message in Private Room**

```
User A sends message in private room

1. User A → POST /api/rooms/{room_id}/messages
   Body: {"content": "Hello!"}

2. Backend:
   - Verify User A is member
   - Create RoomMessage
   - If AI enabled → trigger AI response

3. WebSocket broadcasts to:
   - All room members online
   - AI processes and responds if enabled

4. AI response stored as RoomMessage (sender_type='ai')
```

### **Flow 3: Decline Invite**

```
User B declines invite

1. User B → POST /api/rooms/invites/{invite_id}/decline

2. Backend:
   - Update RoomInvite (status='declined')
   - Notify User A (system message in room)
   - User B never joins room
```

---

## 🌐 API Endpoints

### **Room Management**

```python
POST   /api/rooms                         # Create new room
GET    /api/rooms                         # List user's rooms
GET    /api/rooms/{room_id}               # Get room details
DELETE /api/rooms/{room_id}               # Delete room (creator only)
POST   /api/rooms/{room_id}/leave         # Leave room
```

### **Invites**

```python
POST   /api/rooms/{room_id}/invite        # Invite user to room
GET    /api/rooms/invites/pending         # Get pending invites
POST   /api/rooms/invites/{invite_id}/accept    # Accept invite
POST   /api/rooms/invites/{invite_id}/decline   # Decline invite
```

### **Messages**

```python
GET    /api/rooms/{room_id}/messages      # Get room messages
POST   /api/rooms/{room_id}/messages      # Send message
DELETE /api/rooms/{room_id}/messages/{msg_id}  # Delete message
```

### **Members**

```python
GET    /api/rooms/{room_id}/members       # List room members
DELETE /api/rooms/{room_id}/members/{user_id}  # Remove member (creator only)
```

---

## 🔌 WebSocket Integration

### **Room Channels**

```python
# Connect to room
WS /ws/rooms/{room_id}

# Message format
{
  "type": "room_message",
  "room_id": 123,
  "sender": {
    "id": 456,
    "username": "alice",
    "type": "user"  # or "ai"
  },
  "content": "Hello!",
  "created_at": "2025-10-14T22:00:00Z"
}

# Invite notification
{
  "type": "room_invite",
  "invite_id": 789,
  "room": {
    "id": 123,
    "name": "Chat with Bob"
  },
  "inviter": {
    "id": 456,
    "username": "alice"
  }
}
```

---

## 🤖 AI Integration

### **AI Behavior in Private Rooms:**

1. **Automatic Participation** - AI added as special member (user_id=null, role='ai')
2. **Context Aware** - AI knows:
   - All room members
   - Room purpose
   - Conversation history
   - Individual user profiles

3. **AI Prompts Enhanced:**
```python
system_prompt = f"""
You are in a private group chat with: {member_names}
Room purpose: Help users improve social skills and empathy
Context: This is a {room_type} conversation
Be supportive and help users understand each other better.
"""
```

4. **AI Triggers:**
   - Every message (if ai_enabled=True)
   - On command (@ai or /ai)
   - When explicitly mentioned

---

## 💾 Data Migration

### **Migration Steps:**

1. Create new tables:
   - chat_rooms
   - room_members
   - room_messages
   - room_invites

2. No changes to existing tables

3. Migration script:
```bash
alembic revision --autogenerate -m "Add private chat rooms"
alembic upgrade head
```

---

## 🧪 Testing Strategy

### **Unit Tests:**
- Room creation
- Member management
- Invite acceptance/decline
- Message sending
- AI responses

### **Integration Tests:**
- Full workflow: create → invite → accept → chat
- WebSocket message delivery
- AI participation

### **Manual Testing with You:**
1. Create room via API
2. Send invite
3. Accept invite
4. Chat together
5. Verify AI responds
6. Test via FastAPI /docs

---

## 📊 Frontend Changes Needed

### **Main Chat Window:**
- Show invite messages with [Accept] [Decline] buttons
- List of private rooms in sidebar
- Unread message indicators

### **Room View:**
- Display room members
- Send messages
- See AI responses
- Leave room button

---

## 🎯 Implementation Order

### **Phase 1: Database (Today)**
1. Create data models
2. Run migration
3. Add to data_manager.py

### **Phase 2: Backend API (Today)**
1. Room CRUD endpoints
2. Invite endpoints
3. Message endpoints
4. WebSocket support

### **Phase 3: AI Integration (Today)**
1. Modify ai_chatagent to support rooms
2. Room-aware prompts
3. Multi-user context

### **Phase 4: Testing (Today/Tomorrow)**
1. Unit tests
2. API testing
3. Manual testing with you

---

## ✅ Success Criteria

- [ ] Can create private rooms
- [ ] Can invite users (shows as message)
- [ ] Can accept/decline invites
- [ ] Can send messages in rooms
- [ ] AI responds in rooms
- [ ] Works via API (no frontend needed)
- [ ] WebSocket updates in real-time
- [ ] All tests pass

---

**Ready to implement? Let me know if this design looks good!** 🚀
