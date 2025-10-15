# 🚀 Swagger API Guide - AI/LLM Endpoints

**Date:** 2025-10-15  
**Status:** ✅ Production Ready

---

## 📚 **Access Swagger UI**

### **Local Development:**
```
http://localhost:8000/docs
```

### **Alternative (ReDoc):**
```
http://localhost:8000/redoc
```

---

## 🔐 **Authentication**

All AI endpoints require authentication. 

### **Step 1: Get Access Token**

**Endpoint:** `POST /api/auth/login`

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### **Step 2: Authorize in Swagger**

1. Click the **"Authorize"** button (🔒) in Swagger UI
2. Enter: `Bearer <your_token>`
3. Click **"Authorize"**
4. You're now authenticated! ✅

---

## 🤖 **AI/LLM Endpoints**

### **1. Chat with AI** 
`POST /api/ai/chat`

Send a message to the AI and get a response with tool usage.

**Request:**
```json
{
  "message": "What's the weather in Paris?",
  "conversation_id": "conv_123"
}
```

**Response:**
```json
{
  "response": "The current weather in Paris is 15°C and cloudy.",
  "request_id": "req_abc123def456",
  "conversation_id": "conv_123",
  "tools_used": ["tavily_search"],
  "metrics": {
    "duration_ms": 1234.56,
    "tokens": 2769,
    "cost_usd": 0.000419
  }
}
```

**Capabilities:**
- ✅ Natural language understanding
- ✅ Web search (Tavily)
- ✅ Tool usage (7 tools available)
- ✅ Context management
- ✅ Social skills training
- ✅ Translation & clarification

---

### **2. Manage User Preferences** 
`POST /api/ai/preferences`

Get, set, or delete encrypted user preferences.

**GET Example:**
```json
{
  "action": "get",
  "preference_type": "personal_info"
}
```

**SET Example (Auto-Encrypted):**
```json
{
  "action": "set",
  "preference_type": "personal_info",
  "preference_key": "favorite_color",
  "preference_value": "blue"
}
```

**DELETE Example:**
```json
{
  "action": "delete",
  "preference_type": "personal_info",
  "preference_key": "favorite_color"
}
```

**Response:**
```json
{
  "status": "success",
  "preferences": [
    {
      "preference_type": "personal_info",
      "preference_key": "favorite_color",
      "preference_value": "blue",
      "encrypted": true
    }
  ],
  "total": 1,
  "encryption_enabled": true
}
```

**Encrypted Types:**
- `personal_info` 🔒
- `contact` 🔒
- `financial` 🔒
- `medical` 🔒
- `identification` 🔒
- `private` 🔒

---

### **3. Get Conversation History** 
`GET /api/ai/conversation/history`

Retrieve the last 20 messages for context.

**No request body needed** (uses authenticated user)

**Response:**
```json
{
  "status": "success",
  "messages": [
    {
      "role": "user",
      "content": "Hello!"
    },
    {
      "role": "assistant",
      "content": "Hi! How can I help you today?"
    }
  ],
  "total_messages": 10
}
```

---

### **4. Evaluate Social Skills** 
`POST /api/ai/skills/evaluate`

Analyze a message for social skills with web research.

**Request:**
```json
{
  "message": "I understand how you feel. That makes sense to me.",
  "cultural_context": "Western",
  "use_web_research": true
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Skill evaluation completed with latest research",
  "current_skills": [
    {
      "skill_name": "active_listening",
      "level": 3,
      "progress": 0.75
    },
    {
      "skill_name": "empathy",
      "level": 4,
      "progress": 0.85
    }
  ],
  "message_analysis": {
    "detected_skills": [
      {
        "skill": "active_listening",
        "keywords_found": ["i understand", "that makes sense"]
      },
      {
        "skill": "empathy",
        "keywords_found": ["i understand how you feel"]
      }
    ],
    "skill_count": 2,
    "cultural_context": "Western"
  },
  "latest_standards": {
    "query": "latest Western empathy social skills research 2024 2025",
    "research": "Based on latest research...",
    "updated": "2025-10-15"
  }
}
```

**Evaluated Skills:**
- Active listening 👂
- Empathy ❤️
- Clarity 💬
- Engagement 🤝

**Cultural Contexts:**
- Western
- Eastern
- Latin American
- African
- Middle Eastern

---

### **5. Get AI Metrics** 
`GET /api/ai/metrics?last_n=100`

Retrieve aggregated AI system metrics.

**Query Parameters:**
- `last_n`: Number of recent requests to analyze (default: 100)

**Response:**
```json
{
  "total_requests": 100,
  "success_rate": 0.98,
  "avg_duration_ms": 1234.56,
  "total_tokens": 276900,
  "total_cost_usd": 0.0419,
  "avg_tokens_per_request": 2769.0,
  "most_used_tools": [
    {
      "tool": "tavily_search",
      "count": 45
    },
    {
      "tool": "skill_evaluator",
      "count": 30
    }
  ],
  "duplicate_blocks": 12
}
```

**Use Cases:**
- Cost monitoring 💰
- Performance tracking ⚡
- Tool usage analytics 📊
- Quality assurance ✅

---

### **6. List Available Tools** 
`GET /api/ai/tools`

Get information about all available AI tools.

**Response:**
```json
{
  "total_tools": 7,
  "tools": [
    {
      "name": "tavily_search",
      "description": "Search the internet for current information",
      "available": true
    },
    {
      "name": "user_preference",
      "description": "Manage encrypted user preferences",
      "available": true
    },
    {
      "name": "recall_last_conversation",
      "description": "Retrieve conversation history",
      "available": true
    },
    {
      "name": "skill_evaluator",
      "description": "Evaluate social skills with web research",
      "available": true
    },
    {
      "name": "clarify_communication",
      "description": "Translate and clarify messages",
      "available": true
    },
    {
      "name": "life_event",
      "description": "Track important life events",
      "available": true
    },
    {
      "name": "format_output",
      "description": "Format raw data for humans",
      "available": true
    }
  ]
}
```

---

## 🧪 **Testing Workflow**

### **Complete Test Sequence:**

#### **1. Authenticate**
```bash
POST /api/auth/login
{
  "username": "test_user",
  "password": "test_pass"
}
```

#### **2. List Available Tools**
```bash
GET /api/ai/tools
```

#### **3. Chat with Weather Query**
```bash
POST /api/ai/chat
{
  "message": "What's the weather in Tokyo?",
  "conversation_id": "test_conv_1"
}
```
**Expected:** Uses `tavily_search` tool

#### **4. Save a Preference**
```bash
POST /api/ai/preferences
{
  "action": "set",
  "preference_type": "personal_info",
  "preference_key": "favorite_city",
  "preference_value": "Tokyo"
}
```
**Expected:** Data encrypted ✅

#### **5. Get Preferences**
```bash
POST /api/ai/preferences
{
  "action": "get",
  "preference_type": "personal_info"
}
```
**Expected:** Data decrypted automatically

#### **6. Evaluate Social Skills**
```bash
POST /api/ai/skills/evaluate
{
  "message": "I understand your perspective. That's a valid point.",
  "cultural_context": "Western",
  "use_web_research": true
}
```
**Expected:** Web research for latest standards

#### **7. Get Conversation History**
```bash
GET /api/ai/conversation/history
```
**Expected:** Last 20 messages

#### **8. Check Metrics**
```bash
GET /api/ai/metrics?last_n=10
```
**Expected:** Performance stats & costs

---

## 📊 **Response Codes**

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | Success | Request completed successfully |
| 401 | Unauthorized | Invalid or missing authentication token |
| 400 | Bad Request | Invalid request parameters |
| 500 | Server Error | Internal server error |

---

## 🔍 **O-T-E Observability**

All requests are logged with:

```
2025-10-15 11:48:34 | INFO | AI-ChatAgent | 🚀 Chat request started
  request_id: req_abc123
  user_id: 1

2025-10-15 11:48:35 | INFO | AI-ChatAgent | 🤖 LLM CALL | gpt-4o-mini
  Tokens: 2769 (2760→9) | Cost: $0.000419 | 966.65ms
  request_id: req_abc123
```

**Tracked Metrics:**
- Request ID (for tracing)
- User ID
- Token usage (input/output)
- Cost estimation
- Duration
- Tool usage
- Duplicate blocks

---

## 💡 **Tips & Best Practices**

### **1. Use Conversation IDs**
```json
{
  "conversation_id": "user_123_session_abc"
}
```
Maintains context across requests

### **2. Check Metrics Regularly**
```bash
GET /api/ai/metrics?last_n=1000
```
Monitor costs and performance

### **3. Enable Web Research**
```json
{
  "use_web_research": true
}
```
Get latest standards and information

### **4. Encrypt Sensitive Data**
Use these preference types:
- `personal_info`
- `contact`
- `financial`
- `medical`

### **5. Track Request IDs**
Every response includes `request_id` for debugging

---

## 🚀 **Example: Full Conversation Flow**

```bash
# 1. Login
POST /api/auth/login
{"username": "alice", "password": "secure123"}
→ Get token: "eyJhbG..."

# 2. Authorize in Swagger
Click 🔒 → Enter "Bearer eyJhbG..."

# 3. Start conversation
POST /api/ai/chat
{
  "message": "Hi! Remember my name is Alice",
  "conversation_id": "alice_session_1"
}
→ AI saves preference automatically

# 4. Continue conversation
POST /api/ai/chat
{
  "message": "What's my name?",
  "conversation_id": "alice_session_1"
}
→ AI recalls: "Your name is Alice!"

# 5. Ask for info
POST /api/ai/chat
{
  "message": "What's the weather in Paris?",
  "conversation_id": "alice_session_1"
}
→ Uses tavily_search tool

# 6. Check what AI remembers
GET /api/ai/conversation/history
→ See entire conversation

# 7. View metrics
GET /api/ai/metrics?last_n=10
→ See costs, tools used, performance
```

---

## ✅ **Verification Checklist**

- [ ] Server running: `uvicorn app.main:app --reload`
- [ ] Swagger accessible: http://localhost:8000/docs
- [ ] Can authenticate successfully
- [ ] All 6 AI endpoints visible
- [ ] Chat endpoint returns responses
- [ ] Tools are being used (check `tools_used` in response)
- [ ] Preferences are encrypted (check `encrypted: true`)
- [ ] Conversation history works
- [ ] Metrics endpoint shows data
- [ ] O-T-E logs visible in console

---

## 📚 **Additional Resources**

- **Architecture:** `AI_SYSTEM_ARCHITECTURE.md`
- **O-T-E Documentation:** `OTE_IMPLEMENTATION_COMPLETE.md`
- **Tools Guide:** `AI_TOOLS_COMPLETE.md`
- **Test Suite:** `test_all_tools.py`

---

**Status:** ✅ **READY FOR TESTING**  
**All 6 AI endpoints documented and ready to use!** 🎉
