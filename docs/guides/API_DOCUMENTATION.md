# API Documentation Guide

**Socializer Project**  
**Last Updated:** 2025-10-15

---

## 📋 **Table of Contents**

1. [Overview](#overview)
2. [Accessing API Documentation](#accessing-api-documentation)
3. [API Endpoints by Category](#api-endpoints-by-category)
4. [Testing APIs via Swagger UI](#testing-apis-via-swagger-ui)
5. [Authentication](#authentication)
6. [WebSocket Endpoints](#websocket-endpoints)
7. [Response Formats](#response-formats)
8. [Error Handling](#error-handling)

---

## 🎯 **Overview**

The Socializer API is built with FastAPI and provides:
- **REST API endpoints** for CRUD operations
- **WebSocket endpoints** for real-time communication
- **Interactive documentation** via Swagger UI
- **Auto-generated OpenAPI schema**
- **JWT-based authentication**

---

## 📚 **Accessing API Documentation**

### **Interactive Documentation (Swagger UI)**

Start the server and navigate to:
```
http://localhost:8000/docs
```

**Features:**
- ✅ Browse all API endpoints
- ✅ Test endpoints directly in browser
- ✅ View request/response schemas
- ✅ Copy cURL commands
- ✅ Download OpenAPI spec

### **Alternative Documentation (ReDoc)**

For a cleaner, read-only view:
```
http://localhost:8000/redoc
```

### **OpenAPI Schema (JSON)**

Download the raw schema:
```
http://localhost:8000/openapi.json
```

---

## 🔑 **API Endpoints by Category**

### **1. Authentication** (`/api/auth`)

#### **POST /api/auth/token**
Login and get an access token.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john_doe&password=secretpass123"
```

#### **POST /api/auth/register**
Register a new user account.

**Request:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "secretpass123"
}
```

**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2025-10-15T06:00:00Z"
}
```

#### **POST /api/auth/logout**
Logout and invalidate the current token.

**Request:**
```bash
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

---

### **2. Chat** (`/api/chat`)

#### **WebSocket /ws/{client_id}**
Establish WebSocket connection for real-time chat.

**Parameters:**
- `client_id` (path): Unique identifier for the client
- `token` (query): JWT authentication token

**Connection Example (JavaScript):**
```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://localhost:8000/ws/chat?token=${token}`);

ws.onopen = () => {
  console.log('Connected to chat');
  ws.send(JSON.stringify({
    type: 'chat_message',
    content: 'Hello, World!',
    room_id: 'general'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Message Format (Send):**
```json
{
  "type": "chat_message",
  "content": "Hello, World!",
  "room_id": "general",
  "user_id": 1
}
```

**Message Format (Receive):**
```json
{
  "type": "chat_message",
  "id": "msg_123",
  "content": "Hello, World!",
  "sender_id": 1,
  "sender_name": "john_doe",
  "room_id": "general",
  "timestamp": 1697123456789
}
```

---

### **3. Private Rooms** (`/api/rooms`)

#### **POST /api/rooms/create**
Create a new private chat room.

**Request:**
```json
{
  "name": "Team Discussion",
  "password": "secure123",
  "description": "Private room for team chat"
}
```

**Response:**
```json
{
  "id": "room_abc123",
  "name": "Team Discussion",
  "created_by": 1,
  "created_at": "2025-10-15T06:00:00Z",
  "member_count": 1
}
```

#### **POST /api/rooms/join**
Join a password-protected room.

**Request:**
```json
{
  "room_id": "room_abc123",
  "password": "secure123"
}
```

**Response:**
```json
{
  "success": true,
  "room": {
    "id": "room_abc123",
    "name": "Team Discussion",
    "members": 5
  }
}
```

#### **GET /api/rooms/list**
Get list of available rooms.

**Response:**
```json
{
  "rooms": [
    {
      "id": "room_abc123",
      "name": "Team Discussion",
      "member_count": 5,
      "is_member": true
    },
    {
      "id": "room_def456",
      "name": "Project Planning",
      "member_count": 3,
      "is_member": false
    }
  ]
}
```

---

## 🧪 **Testing APIs via Swagger UI**

### **Step 1: Start the Server**
```bash
# Activate virtual environment
source .venv/bin/activate  # On Mac/Linux
# or
.venv\Scripts\activate  # On Windows

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Step 2: Open Swagger UI**
Navigate to: `http://localhost:8000/docs`

### **Step 3: Authenticate**

1. **Register a test user:**
   - Expand `Authentication` → `POST /api/auth/register`
   - Click "Try it out"
   - Enter test credentials:
     ```json
     {
       "username": "testuser",
       "email": "test@example.com",
       "password": "testpass123"
     }
     ```
   - Click "Execute"

2. **Login to get token:**
   - Expand `Authentication` → `POST /api/auth/token`
   - Click "Try it out"
   - Enter credentials:
     ```
     username: testuser
     password: testpass123
     ```
   - Click "Execute"
   - **Copy the `access_token` from the response**

3. **Authorize Swagger UI:**
   - Click the **🔒 Authorize** button at the top
   - Enter: `Bearer <your_token_here>`
   - Click "Authorize"

### **Step 4: Test Protected Endpoints**

Now you can test any protected endpoint:
- All requests will include your authentication token
- Swagger UI automatically adds `Authorization: Bearer <token>` header

**Example: Create a Room**
1. Expand `Private Rooms` → `POST /api/rooms/create`
2. Click "Try it out"
3. Enter room details
4. Click "Execute"
5. View the response

---

## 🔐 **Authentication**

### **JWT Token Flow**

```
┌─────────┐                 ┌─────────┐
│ Client  │                 │  Server │
└────┬────┘                 └────┬────┘
     │                           │
     │  POST /api/auth/login     │
     │ (username + password)     │
     │──────────────────────────>│
     │                           │
     │    JWT Token              │
     │<──────────────────────────│
     │                           │
     │  Store token in:          │
     │  - localStorage           │
     │  - sessionStorage         │
     │  - Memory (secure)        │
     │                           │
     │  Subsequent Requests      │
     │  Authorization: Bearer    │
     │  <token>                  │
     │──────────────────────────>│
     │                           │
     │    Protected Resource     │
     │<──────────────────────────│
     │                           │
```

### **Token Storage (Security Best Practices)**

**❌ NOT Recommended:**
```javascript
// Storing in localStorage (vulnerable to XSS)
localStorage.setItem('token', token);
```

**✅ Recommended:**
```javascript
// Option 1: HTTP-only cookie (server-side)
// Token set by server in Set-Cookie header

// Option 2: Memory storage (for session duration)
class TokenService {
  constructor() {
    this.token = null;
  }
  
  setToken(token) {
    this.token = token;
    // Store expiry time only
    sessionStorage.setItem('token_expiry', Date.now() + 30 * 60 * 1000);
  }
  
  getToken() {
    const expiry = sessionStorage.getItem('token_expiry');
    if (!expiry || Date.now() > parseInt(expiry)) {
      this.token = null;
      return null;
    }
    return this.token;
  }
}
```

### **Token Refresh**

Tokens expire after 30 minutes. To refresh:

```javascript
async function refreshTokenIfNeeded() {
  const expiry = sessionStorage.getItem('token_expiry');
  const now = Date.now();
  
  // Refresh 5 minutes before expiry
  if (expiry && now > (parseInt(expiry) - 5 * 60 * 1000)) {
    // Re-login to get new token
    const newToken = await login(username, password);
    tokenService.setToken(newToken);
  }
}
```

---

## 🌐 **WebSocket Endpoints**

### **Connection URL Format**
```
ws://localhost:8000/ws/{client_id}?token={jwt_token}
```

### **Message Types**

**1. Chat Message**
```json
{
  "type": "chat_message",
  "content": "Hello!",
  "room_id": "general"
}
```

**2. Typing Indicator**
```json
{
  "type": "typing",
  "is_typing": true,
  "room_id": "general"
}
```

**3. User Status**
```json
{
  "type": "status",
  "status": "online"
}
```

**4. Ping/Pong (Heartbeat)**
```json
{
  "type": "ping",
  "timestamp": 1697123456789
}
```

**Server Response:**
```json
{
  "type": "pong",
  "timestamp": 1697123456789
}
```

---

## 📤 **Response Formats**

### **Success Response**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Resource Name"
  },
  "message": "Operation successful"
}
```

### **Error Response**
```json
{
  "detail": "Error message",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

### **Paginated Response**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

---

## ⚠️ **Error Handling**

### **HTTP Status Codes**

| Code | Meaning | Example |
|------|---------|---------|
| **200** | OK | Successful GET request |
| **201** | Created | Successful POST (created resource) |
| **400** | Bad Request | Invalid input data |
| **401** | Unauthorized | Missing or invalid token |
| **403** | Forbidden | Token valid but insufficient permissions |
| **404** | Not Found | Resource doesn't exist |
| **422** | Unprocessable Entity | Validation error |
| **500** | Internal Server Error | Server-side error |

### **Error Response Examples**

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Authentication Error (401):**
```json
{
  "detail": "Could not validate credentials",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

### **Client-Side Error Handling**

```javascript
async function apiCall(endpoint, options = {}) {
  try {
    const response = await fetch(endpoint, {
      ...options,
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json',
        ...options.headers
      }
    });
    
    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        redirectToLogin();
        throw new Error('Authentication required');
      }
      
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }
    
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}
```

---

## 📊 **Rate Limiting**

**Current Status:** Not implemented  
**Recommended:** Add slowapi for rate limiting

**Future Implementation:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/auth/login")
@limiter.limit("5/minute")  # 5 requests per minute
async def login(request: Request):
    # Login logic
    pass
```

---

## 🔧 **Development Tips**

### **1. Use Swagger UI for Rapid Testing**
- No need for Postman/Insomnia during development
- Test all endpoints directly in browser
- Copy cURL commands for automation

### **2. Monitor WebSocket Connections**
```python
# Add logging in WebSocket endpoint
logger.info(f"WebSocket connection from {client_id}")
logger.info(f"Active connections: {len(manager.active_connections)}")
```

### **3. Enable Debug Mode**
```python
# In main.py
app = FastAPI(
    title="Socializer API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=True  # Enable debug mode for development
)
```

### **4. CORS for Frontend Development**
Already configured for:
- `http://localhost:3000` (React default)
- `http://localhost:8000` (FastAPI)
- `http://127.0.0.1:5500` (Live Server)

---

## 📚 **Additional Resources**

- **FastAPI Documentation:** https://fastapi.tiangolo.com/
- **OpenAPI Specification:** https://swagger.io/specification/
- **WebSocket Protocol:** https://developer.mozilla.org/en-US/docs/Web/API/WebSocket
- **JWT Authentication:** https://jwt.io/introduction

---

## 🎯 **Quick Reference**

### **Common Operations**

**Login and get token:**
```bash
curl -X POST "http://localhost:8000/api/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=myuser&password=mypass"
```

**Use token for authenticated request:**
```bash
curl -X GET "http://localhost:8000/api/rooms/list" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Test WebSocket connection:**
```bash
wscat -c "ws://localhost:8000/ws/chat?token=YOUR_TOKEN_HERE"
```

---

**Last Updated:** 2025-10-15  
**Maintained By:** Socializer Development Team  
**Version:** 1.0
