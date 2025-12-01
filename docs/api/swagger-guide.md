# 📚 Swagger UI User Guide

**Date:** November 12, 2024  
**Server:** http://localhost:8000  
**Swagger UI:** http://localhost:8000/docs

---

## 🚀 HOW TO USE SWAGGER UI

### **Step 1: Start the Server**

```bash
cd /Users/leeroystevenson/PycharmProjects/Socializer
source .venv/bin/activate
uvicorn app.main:app --reload
```

Server will start at: `http://localhost:8000`

---

### **Step 2: Open Swagger UI**

Open in browser: **http://localhost:8000/docs**

You'll see the interactive API documentation with all endpoints.

---

## 🔐 AUTHENTICATION IN SWAGGER

### **Method 1: Using the Authorize Button (Recommended)**

1. **Click the green "Authorize" button** at the top right
2. **Login first to get a token:**
   - Scroll to **POST /api/auth/login**
   - Click "Try it out"
   - Enter credentials:
     ```json
     {
       "username": "human2",
       "password": "FuckShit123."
     }
     ```
   - Click "Execute"
   - **Copy the `access_token`** from the response

3. **Go back to the "Authorize" button**
4. **Paste the token** in the "Value" field like this:
   ```
   Bearer <your_token_here>
   ```
   Example:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

5. **Click "Authorize"**
6. **Click "Close"**

✅ Now all endpoints will use this token automatically!

---

### **Method 2: Manual Token for Each Request**

For each protected endpoint:

1. Click "Try it out"
2. In the **Authorization** header field, enter:
   ```
   Bearer <your_token_here>
   ```
3. Fill in other required fields
4. Click "Execute"

---

## 📋 COMMON WORKFLOWS

### **1. Register a New User**

**Endpoint:** `POST /api/auth/register`

1. Find **POST /api/auth/register** in Swagger
2. Click "Try it out"
3. Fill in form (or use JSON):
   ```json
   {
     "username": "newuser",
     "password": "SecurePass123!",
     "email": "user@example.com"
   }
   ```
4. Click "Execute"
5. Check response (should be 200 or redirect to login)

---

### **2. Login and Get Token**

**Endpoint:** `POST /api/auth/login`

1. Find **POST /api/auth/login**
2. Click "Try it out"
3. Enter JSON:
   ```json
   {
     "username": "human2",
     "password": "FuckShit123."
   }
   ```
4. Click "Execute"
5. **Copy the `access_token`** from response:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI...",
     "token_type": "bearer"
   }
   ```

---

### **3. Get Your User Info**

**Endpoint:** `GET /users/me/`

**Requires:** Authentication

1. Make sure you're authorized (see above)
2. Find **GET /users/me/**
3. Click "Try it out"
4. Click "Execute"
5. View your user information

---

### **4. Chat with AI**

**Endpoint:** `POST /api/ai/chat`

**Requires:** Authentication

1. Make sure you're authorized
2. Find **POST /api/ai/chat**
3. Click "Try it out"
4. Enter message:
   ```json
   {
     "message": "Hello! How are you?"
   }
   ```
5. Click "Execute"
6. View AI response

---

### **5. Get Available Rooms**

**Endpoint:** `GET /api/rooms/`

**Requires:** Authentication

1. Make sure you're authorized
2. Find **GET /api/rooms/**
3. Click "Try it out"
4. Click "Execute"
5. View list of rooms

---

### **6. Create a New Room**

**Endpoint:** `POST /api/rooms/`

**Requires:** Authentication

1. Make sure you're authorized
2. Find **POST /api/rooms/**
3. Click "Try it out"
4. Enter room data:
   ```json
   {
     "name": "My Room",
     "description": "A test room",
     "is_private": false
   }
   ```
5. Click "Execute"
6. View created room info

---

## 🐛 TROUBLESHOOTING

### **Problem: "401 Unauthorized"**

**Solution:**
1. Make sure you've clicked "Authorize" button
2. Make sure your token is valid (not expired)
3. Tokens expire after 1 hour - login again if needed

---

### **Problem: "422 Unprocessable Entity"**

**Solution:**
1. Check request format matches the schema
2. Make sure all required fields are provided
3. Check data types (string vs number, etc.)

---

### **Problem: "Token expired"**

**Solution:**
1. Login again to get a new token
2. Update authorization with new token

---

## 📊 AVAILABLE ENDPOINTS

### **Authentication**
- `POST /api/auth/login` - Login and get token
- `POST /api/auth/register` - Register new user
- `POST /token` - OAuth2 token endpoint
- `POST /logout` - Logout current user

### **User Management**
- `GET /users/me/` - Get current user info
- `GET /api/users/` - Get all users (admin?)

### **Chat**
- `GET /api/chat/messages` - Get chat messages
- `POST /api/chat/send` - Send a chat message
- `POST /chat/` - Alternative chat endpoint

### **AI Integration**
- `POST /api/ai/chat` - Chat with AI
- `POST /api/ai-chat` - Alternative AI chat
- `GET /api/ai/tools` - Get available AI tools
- `POST /api/ai/preferences` - Update AI preferences
- `GET /api/ai/conversation/history` - Get conversation history
- `POST /api/ai/skills/evaluate` - Evaluate skills
- `GET /api/ai/metrics` - Get AI metrics

### **Room Management**
- `GET /api/rooms/` - List all rooms
- `POST /api/rooms/` - Create new room
- `GET /api/rooms/{room_id}` - Get room details
- `DELETE /api/rooms/{room_id}` - Delete room
- `POST /api/rooms/{room_id}/join` - Join room
- `POST /api/rooms/{room_id}/leave` - Leave room
- `GET /api/rooms/{room_id}/members` - Get room members
- `POST /api/rooms/{room_id}/invite` - Invite to room
- `GET /api/rooms/invites/pending` - Get pending invites
- `POST /api/rooms/invites/{invite_id}/accept` - Accept invite
- `POST /api/rooms/invites/{invite_id}/decline` - Decline invite
- `GET /api/rooms/{room_id}/messages` - Get room messages
- `POST /api/rooms/{room_id}/messages` - Send room message

### **Health & Info**
- `GET /health` - Server health check
- `GET /` - Home page
- `GET /login` - Login page
- `GET /register` - Register page

---

## 💡 TIPS FOR SWAGGER UI

### **1. Use the "Authorize" Button**
This is the easiest way - authorize once, use everywhere!

### **2. Expand All Endpoints**
Click section headers to expand/collapse groups of endpoints.

### **3. Check Response Schemas**
Each endpoint shows:
- Required parameters
- Request body format
- Response format
- Possible status codes

### **4. Try Different Status Codes**
Look at "Responses" section to understand:
- 200: Success
- 401: Unauthorized (need to login)
- 422: Validation error (bad request format)
- 500: Server error

### **5. Use "Models" Section**
Scroll down to see data model schemas for requests/responses.

---

## ✅ TEST YOUR SETUP

### **Quick Test:**

1. **Start server:** `uvicorn app.main:app --reload`
2. **Open browser:** http://localhost:8000/docs
3. **Login:** POST /api/auth/login with human2 credentials
4. **Copy token** from response
5. **Click "Authorize"** button
6. **Paste token** as "Bearer <token>"
7. **Try GET /users/me/**
8. **Should return:** Your user info with status 200 ✅

---

## 🎉 YOU'RE READY!

Your Socializer API is fully functional and documented in Swagger UI!

**Features:**
- ✅ Interactive API testing
- ✅ Built-in authentication
- ✅ Auto-generated documentation
- ✅ Request/response examples
- ✅ Schema validation
- ✅ Try it out functionality

**Enjoy exploring your API!** 🚀

