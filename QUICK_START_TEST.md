# 🚀 Quick Start - Test New Features

**Time to Test:** ~5 minutes  
**Features:** Delete Room, Hidden Rooms, AI Monitoring  

---

## ⚡ Quick Test (Copy & Paste)

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Run migration
python migrations/add_room_visibility.py

# 3. Start server
uvicorn app.main:app --reload
```

**Open:** http://localhost:8000/chat

---

## ✅ Test Checklist

### **Test 1: Delete Room** (30 seconds)
1. Click "Private Chat" button
2. Create room named "Test Delete"
3. Look for 🗑️ trash icon on room
4. Click trash icon
5. **✅ Expected:** Confirmation dialog
6. Click OK
7. **✅ Expected:** Room disappears, success toast

---

### **Test 2: Hidden Room** (30 seconds)
1. Click "Private Chat" button
2. Create room named "Secret Room"
3. **Leave "Make room discoverable" UNCHECKED**
4. Click Create
5. **✅ Expected:** 
   - Room appears with 🔐 icon
   - Eye-slash icon visible
   - Console shows `is_public: false`

---

### **Test 3: Public Room** (30 seconds)
1. Click "Private Chat" button
2. Create room named "Public Room"
3. **CHECK "Make room discoverable"**
4. Click Create
5. **✅ Expected:**
   - Room appears
   - Console shows `is_public: true`

---

### **Test 4: AI Monitoring** (15 seconds)
1. Click "Private Chat" button
2. **✅ Expected:** Blue info box explaining AI monitoring
3. Read: "AI Moderator Always Active"
4. Lists: empathy, misunderstandings, cultural context

---

### **Test 5: Creator-Only Delete** (30 seconds)
1. User A creates room, invites User B
2. User B accepts
3. User B views room in list
4. **✅ Expected:** No delete button for User B

---

## 🔍 Console Logs

**What you should see:**

```javascript
// Creating hidden room (default)
[TRACE] handleCreateRoom: creating room {
  name: "Secret Room",
  is_public: false,  // ✅
  ...
}

// Deleting room
[TRACE] deleteRoom: { room_id: 1, name: "Test Delete" }
[TRACE] deleteRoom: success

// Backend
[TRACE] create_room: ... public=False
[TRACE] delete_room: room 1 deleted by user 2
```

---

## 🐛 If Something Fails

### **Migration fails:**
```bash
# Check if column already exists
sqlite3 data.sqlite.db "PRAGMA table_info(chat_rooms);"
# Look for is_public in output
```

### **Delete button not showing:**
- Check: Are you the room creator?
- Check console: `currentUserId` matches `room.creator_id`?

### **Rooms not loading:**
- Check console for errors
- Check backend logs: `[TRACE] loadRooms`
- Verify API response has `is_public` field

---

## ✅ Success!

**All tests passing?** Commit your changes:

```bash
git add .
git commit -m "feat: Delete room, hidden rooms, AI monitoring

- Delete button for room creators
- Hidden rooms by default (invite-only)
- Public rooms option (future discovery)
- AI monitoring always active"
```

---

**Total Time:** ~5 minutes to test everything! 🎉
