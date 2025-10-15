# 🚀 Quick Test Guide - Private Rooms

**Server Status:** ✅ Running on port 8000

---

## 1️⃣ Open the Chat

```
http://localhost:8000/chat
```

---

## 2️⃣ What You Should See

### **Left Sidebar (Top Section):**
```
┌─────────────────────────┐
│ 🟣 Private Rooms        │
├─────────────────────────┤
│                         │
│  No private rooms yet   │  ← If no rooms
│                         │
├─────────────────────────┤
│ 🟢 Online Users         │
├─────────────────────────┤
```

### **Top Right:**
```
[ 🟣 Private Chat ]  [ Logout ]
       ↑
  Click this!
```

---

## 3️⃣ Create Your First Room

1. Click **"Private Chat"** button (top right)

2. **Modal Opens** - Fill the form:
   ```
   Room Name: Test Room 1 (or leave empty)
   
   [✓] Password Protected  ← Toggle on/off
       Password: mypass123   (if enabled)
   
   [✓] Enable AI Assistant  ← Toggle on/off
   
   Invite Users: (select from list)
   ```

3. Click **"Create Room"**

4. **Success!** You should see:
   - Green toast: "Room created successfully!"
   - Room appears in sidebar
   - Room is auto-selected (highlighted)

---

## 4️⃣ Check the Console

Open DevTools (F12) → Console tab:

```javascript
✅ Should see these logs:

[TRACE] User data loaded: { username: "...", id: ... }
[TRACE] PrivateRooms.js loaded
[TRACE] PrivateRoomsManager initialized
[CHAT] Initializing private rooms manager...
[TRACE] loadRooms: fetching rooms
[TRACE] loadRooms: success { count: 1 }
[TRACE] renderRooms: rendering { count: 1 }
[TRACE] Private chat button clicked
[TRACE] handleCreateRoom: creating room
[TRACE] handleCreateRoom: room created { room_id: 1 }
[TRACE] showSuccess: Room "Test Room 1" created successfully!
```

---

## 5️⃣ Test Room Features

### **Test 1: Password Protection**
```
1. Click "Private Chat"
2. Check "Password Protected"
3. Enter password: "secret123"
4. Create room
5. Verify: 🔒 icon appears next to room name
```

### **Test 2: AI Assistant**
```
1. Click "Private Chat"
2. Check "Enable AI Assistant"
3. Create room
4. Verify: 🤖 icon appears next to room name
```

### **Test 3: Room Selection**
```
1. Click different rooms in sidebar
2. Verify: Selected room has gradient background
3. Verify: Chat header updates with room name
4. Verify: Console logs room selection
```

### **Test 4: Multiple Rooms**
```
1. Create 3-4 different rooms
2. Verify: All appear in scrollable list
3. Verify: Can select each one
4. Verify: Icons show correctly (🔒/🤖/💬)
```

---

## 6️⃣ Expected Behavior

### **Room Item Display:**
```
┌────────────────────────────────┐
│ 🔒 Team Project                │
│    👥 3 • 🔒 • 🤖              │  ← 3 members, locked, AI
└────────────────────────────────┘
```

### **Active Room (Selected):**
```
┌────────────────────────────────┐
│ 🔒 Team Project                │ ← Purple gradient
│    👥 3 • 🔒 • 🤖              │   White text
└────────────────────────────────┘
```

### **Chat Header Updates:**
```
Before: General Chat
        Everyone can join this chat

After:  Team Project
        3 members • Password protected • AI enabled
```

---

## 7️⃣ Common Issues & Fixes

### **Modal doesn't open:**
```
Fix: Check console for errors
     Verify Bootstrap loaded
     Hard refresh (Cmd+Shift+R)
```

### **Rooms don't load:**
```
Fix: Check token: console.log(window.ACCESS_TOKEN)
     Check Network tab for /api/rooms/ call
     Verify response is 200 OK
```

### **Create fails:**
```
Fix: Check form validation
     If password checked, must fill password field
     Check Network tab for error response
```

### **Rooms list empty:**
```
Normal! No rooms exist yet.
Create your first room!
```

---

## 8️⃣ API Endpoints Being Called

When you use the UI, these are called:

```
1. Page Load:
   GET /api/rooms/
   → Returns: [{ id: 1, name: "...", ... }]

2. Create Room:
   POST /api/rooms/
   Body: { name, password, ai_enabled }
   → Returns: { id: 1, name: "...", ... }

3. Send Invites:
   POST /api/rooms/1/invite
   Body: { user_ids: [2, 3] }
   → Returns: { message: "..." }

4. Load Users (for invites):
   GET /api/users/
   → Returns: [{ id: 1, username: "..." }]
```

---

## 9️⃣ What's NOT Implemented Yet

These will come next:

- ❌ Switch WebSocket to room channel
- ❌ Display room-specific messages
- ❌ Accept/decline invites UI
- ❌ Leave room button
- ❌ Edit/delete room

**Current:** Room creation and listing works!  
**Next:** Room chat messaging

---

## 🎯 Success Criteria

✅ **Working if you see:**
- [ ] Private Rooms section in sidebar
- [ ] Private Chat button opens modal
- [ ] Can create rooms with name
- [ ] Can create rooms without name (auto-generated)
- [ ] Can toggle password on/off
- [ ] Can toggle AI on/off
- [ ] Room appears in sidebar after creation
- [ ] Room icons show correctly (🔒/🤖)
- [ ] Can select rooms (highlight changes)
- [ ] Chat header updates on selection
- [ ] Console shows [TRACE] logs
- [ ] Toast shows on success/error

---

## 📸 Visual Reference

**Before (Main Chat):**
```
┌─────────────────────────────────────┐
│ Socializer Chat  [Private Chat] [X] │ ← Button here
├─────────────────────────────────────┤
│ Online Users │ General Chat         │
│ • Alice      │ (messages)           │
│ • Bob        │                      │
└─────────────────────────────────────┘
```

**After (With Rooms):**
```
┌─────────────────────────────────────┐
│ Socializer Chat  [Private Chat] [X] │
├─────────────────────────────────────┤
│ Private Rooms│ Team Project         │ ← Room name
│ 💬 General   │ 3 members • 🔒 • 🤖  │ ← Info
│ 🔒 Team      │                      │
│ 🤖 AI Study  │ (room messages)      │
├──────────────┤                      │
│ Online Users │                      │
│ • Alice      │                      │
└─────────────────────────────────────┘
```

---

## 🎉 That's It!

**Ready to test?**

1. Open: `http://localhost:8000/chat`
2. Click: "Private Chat" button
3. Create: Your first room!
4. Check: Console for logs
5. Enjoy: The new feature! 🚀

**Report any issues you find!**
