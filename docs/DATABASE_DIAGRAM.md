# Socializer Database Schema Diagram

## 📊 Visual Database Structure

### How to View the Interactive Diagram

1. **Visit**: https://dbdiagram.io/d
2. **Import**: Click "Import" → "From DBML"
3. **Paste**: Copy the contents of `database_schema.dbml`
4. **View**: Explore the interactive, color-coded diagram

---

## 🗂️ Database Overview (12 Tables)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SOCIALIZER DATABASE SCHEMA                        │
│                                                                       │
│  🔐 Security & Auth  │  👤 Users & Skills  │  💬 Chat System        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📐 Entity Relationship Diagram (Simplified)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                                                                              │
│                             ┌────────────────┐                              │
│                             │     users      │                              │
│                             │  (Core User)   │                              │
│                             └───────┬────────┘                              │
│                                     │                                        │
│                  ┌──────────────────┼──────────────────┐                    │
│                  │                  │                  │                    │
│         ┌────────▼────────┐ ┌──────▼──────┐  ┌────────▼────────┐          │
│         │ token_blacklist │ │ error_logs  │  │ user_preferences│          │
│         │   (Security)    │ │  (Logging)  │  │ (AI Learning)   │          │
│         └─────────────────┘ └─────────────┘  └─────────────────┘          │
│                                     │                                        │
│                  ┌──────────────────┼──────────────────┐                    │
│                  │                  │                  │                    │
│         ┌────────▼────────┐ ┌──────▼──────┐  ┌────────▼────────┐          │
│         │  user_skills    │ │  training   │  │   chat_rooms    │          │
│         │  (Proficiency)  │ │ (Progress)  │  │  (Rooms List)   │          │
│         └────────┬────────┘ └──────┬──────┘  └────────┬────────┘          │
│                  │                  │                  │                    │
│         ┌────────▼────────┐         │         ┌────────▼────────┐          │
│         │     skills      │         │         │  room_members   │          │
│         │   (Catalog)     │◄────────┘         │  (Membership)   │          │
│         └─────────────────┘                   └────────┬────────┘          │
│                                                         │                    │
│                                                ┌────────┼────────┐          │
│                                                │        │        │          │
│                                       ┌────────▼──┐ ┌──▼────────▼───┐     │
│                                       │ room_msgs │ │ room_invites  │     │
│                                       │ (Convers.)│ │  (Requests)   │     │
│                                       └───────────┘ └───────────────┘     │
│                                                                              │
│                                       ┌──────────────────┐                  │
│                                       │general_chat_msgs │                  │
│                                       │ (Public Chat)    │                  │
│                                       └──────────────────┘                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Relationships

### 1️⃣ User-Centric Relationships
```
users (1) ──── (*) token_blacklist      [JWT revocation]
users (1) ──── (*) error_logs            [Error tracking]
users (1) ──── (*) user_preferences      [AI-learned preferences]
users (1) ──── (*) user_skills           [Skill proficiency]
users (1) ──── (*) training              [Active training]
users (1) ──── (*) chat_rooms            [Created rooms]
users (1) ──── (*) room_members          [Room participation]
users (1) ──── (*) room_messages         [Sent messages]
users (1) ──── (*) general_chat_messages [Public messages]
users (1) ──── (*) room_invites (2x)     [Sent & received invites]
```

### 2️⃣ Skills System
```
skills (1) ──── (*) user_skills    [User proficiency in each skill]
skills (1) ──── (*) training       [Training sessions for skills]

user_skills:
  - Composite unique key: (user_id, skill_id)
  - Tracks level: 0-10

training:
  - Composite primary key: (user_id, skill_id)
  - Tracks progress: 0.0-1.0
```

### 3️⃣ Chat System
```
chat_rooms (1) ──── (*) room_members    [Who's in the room]
chat_rooms (1) ──── (*) room_messages   [Conversation history]
chat_rooms (1) ──── (*) room_invites    [Pending invitations]

room_messages (1) ──── (0-1) room_invites [Invite message link]
```

---

## 📋 Table Details

### 🔐 Security & Authentication

#### `users` - Core User Table
- **Primary Key**: `id`
- **Unique**: `username`, `hashed_email`
- **Encryption**: `encryption_key` (Fernet key per user)
- **Memory**: `conversation_memory` (encrypted blob)
- **LLM Config**: Custom provider/endpoint/model

#### `token_blacklist` - JWT Revocation
- **Purpose**: Track invalidated JWT tokens
- **Foreign Key**: `user_id` → `users.id`
- **Cleanup**: Expired tokens can be purged

#### `error_logs` - Application Errors
- **Purpose**: Centralized error tracking
- **Foreign Key**: `user_id` → `users.id` (optional)
- **Context**: JSON field for debugging

---

### 👤 Skills & Training

#### `skills` - Skills Catalog
- **Primary Key**: `id`
- **Unique**: `skill_name`
- **Examples**: empathy, active_listening, communication

#### `user_skills` - User Proficiency
- **Composite Unique**: `(user_id, skill_id)`
- **Foreign Keys**: 
  - `user_id` → `users.id` (CASCADE)
  - `skill_id` → `skills.id` (CASCADE)
- **Level**: 0-10 proficiency scale

#### `training` - Active Training Sessions
- **Composite Primary Key**: `(user_id, skill_id)`
- **Foreign Keys**: 
  - `user_id` → `users.id` (CASCADE)
  - `skill_id` → `skills.id` (CASCADE)
- **Progress**: 0.0-1.0 completion percentage
- **Status**: pending/active/completed

#### `user_preferences` - AI-Learned Preferences
- **Composite Unique**: `(user_id, preference_type, preference_key)`
- **Foreign Key**: `user_id` → `users.id` (CASCADE)
- **Structure**: Type.Key → JSON Value
- **Confidence**: 0.0-1.0 confidence score

---

### 💬 Chat System

#### `chat_rooms` - Chat Rooms
- **Primary Key**: `id`
- **Foreign Key**: `creator_id` → `users.id`
- **Types**: direct, group, private
- **Features**: AI-enabled, password-protected, public/private

#### `room_members` - Room Membership
- **Composite Unique**: `(room_id, user_id)`
- **Foreign Keys**:
  - `room_id` → `chat_rooms.id` (CASCADE)
  - `user_id` → `users.id` (NULL for AI)
- **Roles**: creator, member, ai
- **Tracking**: `last_read_at` for unread messages

#### `room_messages` - Chat Messages
- **Primary Key**: `id`
- **Foreign Keys**:
  - `room_id` → `chat_rooms.id` (CASCADE)
  - `sender_id` → `users.id` (NULL for AI)
- **Types**: text, invite, system
- **Features**: Edit/delete support, metadata

#### `general_chat_messages` - Public Chat
- **Primary Key**: `id`
- **Foreign Key**: `sender_id` → `users.id`
- **Purpose**: Main public chatroom messages

#### `room_invites` - Room Invitations
- **Composite Unique**: `(room_id, invitee_id)`
- **Foreign Keys**:
  - `room_id` → `chat_rooms.id` (CASCADE)
  - `inviter_id` → `users.id`
  - `invitee_id` → `users.id`
  - `message_id` → `room_messages.id` (optional)
- **Status**: pending/accepted/declined

---

## 🎨 Color Coding (on dbdiagram.io)

When you import to dbdiagram.io, tables are grouped by color:

- 🔵 **Blue**: Core user & authentication tables
- 🟢 **Green**: Skills & training system
- 🟣 **Purple**: Chat & messaging system
- 🟡 **Yellow**: Preferences & personalization
- 🔴 **Red**: Logging & security

---

## 📊 Database Statistics

| Category | Tables | Key Features |
|----------|--------|--------------|
| **Users & Auth** | 3 | Encryption, JWT blacklist, error logging |
| **Skills System** | 4 | Skills catalog, proficiency tracking, training progress |
| **Chat System** | 5 | Multi-room, AI-enabled, invitations, public/private |
| **Total Tables** | 12 | Fully normalized, CASCADE deletes |

---

## 🔍 Key Design Decisions

### 1. User Privacy & Security
✅ **Per-user encryption keys**
- Each user has unique Fernet key
- Conversation memory encrypted at rest
- Privacy-hashed emails and names

### 2. Skills & Training
✅ **Flexible skill system**
- Skills catalog separate from user proficiency
- Multiple training sessions per user
- Progress tracking with timestamps

✅ **Composite primary keys**
- `training(user_id, skill_id)` prevents duplicates
- One active training per user-skill pair

### 3. Chat Architecture
✅ **Multi-room support**
- Public general chat + private rooms
- AI can be member of any room
- Invite system with status tracking

✅ **Message types**
- User messages
- AI responses
- System notifications

### 4. Data Integrity
✅ **CASCADE deletes**
- Delete user → deletes all related records
- Clean orphan prevention

✅ **Unique constraints**
- Prevent duplicate skills per user
- Prevent duplicate room memberships
- Prevent duplicate invitations

---

## 🚀 Usage Examples

### Creating a New User with Training
```sql
-- 1. Create user
INSERT INTO users (username, hashed_password, hashed_email, encryption_key)
VALUES ('alice', 'hashed_pw', 'hashed_email', 'fernet_key');

-- 2. Add skills to catalog (if not exist)
INSERT INTO skills (skill_name) VALUES ('empathy'), ('active_listening');

-- 3. Initialize user skills
INSERT INTO user_skills (user_id, skill_id, level)
VALUES (1, 1, 0), (1, 2, 0);

-- 4. Start training
INSERT INTO training (user_id, skill_id, status, progress)
VALUES (1, 1, 'active', 0.0);
```

### Creating a Private Chat Room
```sql
-- 1. Create room
INSERT INTO chat_rooms (creator_id, room_type, ai_enabled)
VALUES (1, 'private', true);

-- 2. Add members
INSERT INTO room_members (room_id, user_id, role)
VALUES (1, 1, 'creator'), (1, 2, 'member'), (1, NULL, 'ai');

-- 3. Send invitation
INSERT INTO room_invites (room_id, inviter_id, invitee_id)
VALUES (1, 1, 2);
```

---

## 📈 Query Patterns

### Get User's Training Progress
```sql
SELECT 
  u.username,
  s.skill_name,
  t.progress,
  t.status,
  us.level as current_level
FROM training t
JOIN users u ON t.user_id = u.id
JOIN skills s ON t.skill_id = s.id
LEFT JOIN user_skills us ON us.user_id = t.user_id AND us.skill_id = t.skill_id
WHERE u.id = 1;
```

### Get Room Messages with Sender Info
```sql
SELECT 
  rm.id,
  rm.content,
  rm.created_at,
  rm.sender_type,
  u.username as sender_name
FROM room_messages rm
LEFT JOIN users u ON rm.sender_id = u.id
WHERE rm.room_id = 1
  AND rm.is_deleted = false
ORDER BY rm.created_at DESC
LIMIT 50;
```

### Get User's Active Room Invites
```sql
SELECT 
  ri.id,
  cr.name as room_name,
  u.username as inviter_name,
  ri.created_at
FROM room_invites ri
JOIN chat_rooms cr ON ri.room_id = cr.id
JOIN users u ON ri.inviter_id = u.id
WHERE ri.invitee_id = 1
  AND ri.status = 'pending';
```

---

## 🎯 Next Steps

1. **View Interactive Diagram**
   - Open `database_schema.dbml` in dbdiagram.io
   - Explore relationships visually
   - Export as PNG/PDF for documentation

2. **Generate Migration Scripts**
   - dbdiagram.io can export to SQL
   - Choose your database dialect
   - Review and customize

3. **Document Custom Queries**
   - Add common queries to this file
   - Document performance considerations
   - Note any indexes needed

---

## 📝 Notes

- **SQLite Compatibility**: Schema designed for SQLite but portable
- **Cascade Deletes**: Configured for clean user removal
- **Indexes**: Primary keys and frequently queried fields indexed
- **JSON Fields**: Used for flexible storage (preferences, metadata)
- **Timestamps**: Consistent use of `datetime` for audit trails

---

**Generated**: November 30, 2025  
**Database Version**: 1.0.0  
**Schema File**: `database_schema.dbml`
