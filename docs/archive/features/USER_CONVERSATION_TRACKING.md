# 📝 User-Specific Conversation Tracking

**Date:** 2025-10-16  
**Status:** ✅ Implemented

---

## 📋 Overview

The Socializer app now tracks **user-specific conversation history**, including both:
1. **AI conversations** (`/ai` commands)
2. **General chat messages** (WebSocket chat)

Each user's history is **private** and **isolated** - users can only recall their own messages.

---

## 🔧 How It Works

### **Message Types**

Messages are saved with a `type` field to distinguish them:

```json
{
  "role": "user",
  "content": "Hello, world!",
  "type": "chat",           // "chat" or "ai"
  "room_id": "general",     // Only for chat messages
  "timestamp": "2025-10-16T00:00:00Z",
  "tools_used": ["tavily_search"]  // Only for AI responses
}
```

---

## 💾 Where Messages Are Saved

### **1. General Chat Messages (WebSocket)**

**File:** `app/websocket/routes.py`

When a user sends a chat message:
```python
dm.save_messages(user_id, [
    {
        "role": "user",
        "content": "Hello everyone!",
        "type": "chat",
        "room_id": "general",
        "timestamp": "2025-10-16T00:00:00Z"
    }
])
```

**Saved:**
- ✅ Messages the user **SENDS**
- ❌ Messages from other users (privacy)
- ✅ Room context (room_id)
- ✅ Timestamp

---

### **2. AI Conversations**

**File:** `app/ai_manager.py`

When a user interacts with AI:
```python
dm.save_messages(user_id, [
    {
        "role": "user",
        "content": "What's the weather?",
        "type": "ai",
        "timestamp": "2025-10-16T00:00:00Z"
    },
    {
        "role": "assistant",
        "content": "It's sunny in Paris...",
        "type": "ai",
        "tools_used": ["tavily_search", "format_output"],
        "timestamp": "2025-10-16T00:00:01Z"
    }
])
```

**Saved:**
- ✅ User's question
- ✅ AI's response
- ✅ Tools used by AI
- ✅ Timestamps

---

## 🔍 Retrieving Conversation History

### **Using the ConversationRecallTool**

```python
from tools.conversation_recall_tool import ConversationRecallTool
from datamanager.data_manager import DataManager

dm = DataManager("database.db")
tool = ConversationRecallTool(dm)

result = tool.invoke(user_id=1)
```

**Response:**
```json
{
  "status": "success",
  "message": "Conversation retrieved successfully",
  "data": [
    {"role": "user", "content": "Hello!", "type": "chat", "room_id": "general"},
    {"role": "user", "content": "What's the weather?", "type": "ai"},
    {"role": "assistant", "content": "It's sunny...", "type": "ai", "tools_used": ["tavily_search"]}
  ],
  "total_messages": 50,
  "returned_messages": 10,
  "ai_messages": 6,
  "chat_messages": 4
}
```

---

## 🛡️ Privacy & Security

### **What's Saved**
- ✅ User's **OWN** messages only
- ✅ User's **OWN** AI interactions
- ❌ **NOT** other users' messages
- ❌ **NOT** messages user received (only sent)

### **Isolation**
- Each user's history is stored in `users.messages` (their row only)
- No cross-user data access
- `recall_last_conversation` requires `user_id` parameter

---

## 📊 Database Schema

### **User Table**

```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    messages = Column(Text)  # JSON string: List[Dict]
    # ... other fields
```

### **Messages Field Format**

```json
[
  {
    "role": "user",
    "content": "Message 1",
    "type": "chat",
    "room_id": "general",
    "timestamp": "2025-10-16T00:00:00Z"
  },
  {
    "role": "user",
    "content": "Message 2",
    "type": "ai",
    "timestamp": "2025-10-16T00:01:00Z"
  },
  {
    "role": "assistant",
    "content": "Response 2",
    "type": "ai",
    "tools_used": ["tavily_search"],
    "timestamp": "2025-10-16T00:01:01Z"
  }
]
```

**Storage Limit:**
- Keeps last 10 messages to prevent database bloat
- Older messages are automatically pruned

---

## 🔄 Message Flow

### **Chat Message Flow**

```mermaid
User types message
    ↓
WebSocket receives
    ↓
Save to user's history (type="chat")
    ↓
Broadcast to room
    ↓
Other users see message
```

### **AI Conversation Flow**

```mermaid
User sends /ai command
    ↓
AI processes request
    ↓
Save user question + AI response (type="ai")
    ↓
Return response to user
```

---

## 🧪 Testing

### **Test Chat History Saving**

```python
# Send a chat message
# Via WebSocket: {"type": "chat", "text": "Hello!"}

# Check it was saved
dm = DataManager("database.db")
user = dm.get_user(user_id=1)
messages = json.loads(user.messages)

# Should include:
assert messages[-1]["content"] == "Hello!"
assert messages[-1]["type"] == "chat"
assert messages[-1]["room_id"] == "general"
```

### **Test AI History Saving**

```python
# Send AI command
# POST /api/ai/chat: {"message": "What's the weather?"}

# Check it was saved
messages = json.loads(user.messages)

# Should include:
assert messages[-2]["content"] == "What's the weather?"
assert messages[-2]["type"] == "ai"
assert messages[-1]["role"] == "assistant"
assert messages[-1]["type"] == "ai"
assert "tools_used" in messages[-1]
```

### **Test Recall Tool**

```python
tool = ConversationRecallTool(dm)
result = json.loads(tool.invoke(user_id=1))

assert result["status"] == "success"
assert len(result["data"]) <= 10
assert result["ai_messages"] + result["chat_messages"] == len(result["data"])
```

---

## 🎯 Use Cases

### **1. Context Recall**
```
User: /ai What did I say about the weather earlier?
AI: [Uses recall_last_conversation] You asked "What's the weather in Paris?"
```

### **2. Conversation Summary**
```
User: /ai Summarize our conversation
AI: [Uses recall_last_conversation] We discussed weather, your preferences...
```

### **3. History Search**
```
User: /ai Did I mention dogs?
AI: [Uses recall_last_conversation] Yes, you said "I love dogs" in general chat
```

---

## 🐛 Troubleshooting

### **Messages Not Saving**

**Check:**
1. User is authenticated (`user_id` is valid)
2. Database is writable
3. No exceptions in server logs

**Debug:**
```python
dm = DataManager("database.db")
user = dm.get_user(user_id=1)
print(f"Messages: {user.messages}")
```

### **Recall Returns Empty**

**Check:**
1. User has sent messages
2. `user.messages` is not `None` or `"[]"`
3. JSON is valid

**Debug:**
```python
tool = ConversationRecallTool(dm)
result = json.loads(tool.invoke(user_id=1))
print(f"Status: {result['status']}")
print(f"Total: {result.get('total_messages', 0)}")
```

---

## 📈 Performance

### **Message Limit**
- **Stored:** Last 10 messages per user
- **Recalled:** Last 10 messages (configurable)
- **Why:** Prevent database bloat

### **Optimization**
- Messages stored as JSON in single field (no joins needed)
- Indexed by `user_id` for fast lookup
- Automatic pruning of old messages

---

## 🚀 Future Enhancements

### **Possible Improvements**
1. **Full-text search** in conversation history
2. **Date range filters** for recall
3. **Export conversation** to JSON/PDF
4. **Analytics** on message types
5. **Sentiment analysis** over time
6. **Room-specific recall** (filter by room_id)

### **Configuration Options**
```python
# In config.py (future)
MAX_MESSAGES_STORED = 10  # Current: 10
MAX_MESSAGES_RECALLED = 10  # Current: 10
ENABLE_CHAT_TRACKING = True  # Toggle feature
ENABLE_AI_TRACKING = True
```

---

## ✅ Summary

**What Changed:**
- ✅ WebSocket now saves user's chat messages
- ✅ AI conversations marked with metadata
- ✅ `recall_last_conversation` returns both types
- ✅ Privacy-preserving (user-specific only)

**Benefits:**
- 🎯 Better context for AI
- 💾 Persistent conversation memory
- 🔍 Searchable history
- 🔒 Privacy-focused design

**Files Modified:**
- `app/websocket/routes.py` - Chat message saving
- `app/ai_manager.py` - AI conversation metadata
- `datamanager/data_manager.py` - Metadata preservation
- `tools/conversation_recall_tool.py` - Enhanced recall

---

**Ready for Testing!** 🎉

Try:
1. Send chat messages
2. Use `/ai` commands
3. Ask: `/ai What did I say earlier?`
4. Check: AI recalls both chat and AI history!
