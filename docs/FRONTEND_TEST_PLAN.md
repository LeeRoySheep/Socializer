# Frontend Test Plan - Chat Application

**Status:** In Progress  
**Last Updated:** 2025-10-07  
**Server Status:** ✅ Stable (CPU: 0.0%)

---

## ✅ Backend Fixes Completed

1. ✅ Fixed ping/pong logic (send BEFORE timeout check)
2. ✅ Fixed infinite loop on disconnect (RuntimeError handler)
3. ✅ Fixed missing `await` on `disconnect()` method
4. ✅ Removed duplicate methods in `chat_manager.py`
5. ✅ Added debug logging for ping/pong

---

## 🎯 Frontend Test Objectives

Test all chat functionality systematically to ensure:
- WebSocket connection stability
- Message sending/receiving
- User presence (online/offline status)
- Typing indicators
- Logout/reconnection handling
- UI responsiveness

---

## 📋 Test Plan - Step by Step

### **PHASE 1: Connection & Authentication** ✅

#### Test 1.1: Initial Connection
- [x] Navigate to `/login`
- [x] Login with valid credentials
- [x] Verify WebSocket establishes connection
- [x] Verify "Welcome to the chat" message appears
- [x] Verify online users list populates
- [x] **Result:** PASSED

#### Test 1.2: Ping/Pong Keep-Alive ✅
- [x] Stay connected for 60+ seconds
- [x] Verify ping messages sent every 30 seconds
- [x] Verify pong responses received
- [x] Verify connection stays alive (tested 180s+)
- [x] **Result:** PASSED - 6 ping/pong cycles, no disconnect
- [x] **Expected Console Output:**
  ```javascript
  Sending ping: {"type":"ping",...}
  Received pong
  ```

---

### **PHASE 2: Message Functionality** ⏳

#### Test 2.1: Send Message ✅
- [x] Type a message in the input field
- [x] Click send or press Enter
- [x] Verify message appears in chat window
- [x] Verify message shows correct username
- [x] Verify timestamp is displayed
- [x] Input field clears after send
- [x] **Result:** PASSED - Both Enter key and Send button work
- [x] **Fix Applied:** Added missing `<form>` wrapper to HTML

#### Test 2.2: Receive Message (Multi-User) ✅
- [x] Open second browser/incognito window
- [x] Login with different user
- [x] Send message from User 2
- [x] Verify User 1 receives the message
- [x] Verify correct sender name displayed
- [x] Verify bi-directional messaging works
- [x] **Result:** PASSED - Real-time message delivery working perfectly

#### Test 2.3: Message Persistence
- [ ] Send 10 messages
- [ ] Scroll through chat history
- [ ] Verify all messages visible
- [ ] Verify correct order (oldest to newest)

---

### **PHASE 3: Typing Indicators** ⏳

#### Test 3.1: Send Typing Indicator
- [ ] Start typing in message input
- [ ] Verify typing indicator sent to server
- [ ] Stop typing
- [ ] Verify typing indicator cleared
- [ ] **Expected Console:**
  ```javascript
  📤 Sent: {type: "typing", is_typing: true}
  📤 Sent: {type: "typing", is_typing: false}
  ```

#### Test 3.2: Receive Typing Indicator
- [ ] User 2 starts typing
- [ ] Verify User 1 sees "User2 is typing..." indicator
- [ ] User 2 stops typing
- [ ] Verify typing indicator disappears
- [ ] **Expected:** Visual feedback in UI

---

### **PHASE 4: User Presence** ⏳

#### Test 4.1: Online Users List
- [ ] Verify current user appears in online list
- [ ] User 2 logs in
- [ ] Verify User 2 appears in online list
- [ ] Verify user count increases
- [ ] **Expected:** Real-time list updates

#### Test 4.2: User Joins Notification
- [ ] User 2 logs in
- [ ] Verify "User2 has joined" message in chat
- [ ] Verify system message styling (different from chat)
- [ ] **Expected:** System message appears

#### Test 4.3: User Leaves Notification
- [ ] User 2 logs out
- [ ] Verify "User2 has left" message in chat
- [ ] Verify User 2 removed from online list
- [ ] **Expected:** Real-time presence updates

---

### **PHASE 5: Logout & Cleanup** ⏳

#### Test 5.1: Normal Logout ✅
- [x] Click logout button
- [x] Verify WebSocket closes cleanly (code 1000)
- [x] Verify no reconnection attempts
- [x] Verify redirect to login page
- [x] Verify server CPU stays normal (< 5%)
- [x] **Result:** PASSED - Clean logout, code 1000
- [x] **Fixes Applied:** 
  - Added WebSocketDisconnect exception handler
  - Exclude disconnected client from broadcast

#### Test 5.2: Server-Side Verification ✅
- [x] Check server terminal after logout
- [x] Verify "WebSocket disconnected" log
- [x] Verify no error spam
- [x] Verify no RuntimeError messages
- [x] **Result:** PASSED - No errors in server logs

#### Test 5.3: Multiple Logout Cycles
- [ ] Login → Logout (repeat 3 times)
- [ ] Verify server stays stable each time
- [ ] Verify no memory leaks
- [ ] Verify no connection buildup
- [ ] **Expected:** Stable server (CPU < 5%)

---

### **PHASE 6: Edge Cases & Error Handling** ⏳

#### Test 6.1: Network Interruption
- [ ] Establish connection
- [ ] Kill server (simulate network loss)
- [ ] Verify reconnection attempts start
- [ ] Restart server
- [ ] Verify connection re-establishes
- [ ] Verify messages sent after reconnect
- [ ] **Expected:** Max 5 reconnection attempts

#### Test 6.2: Invalid Token Handling
- [ ] Manually clear localStorage token
- [ ] Try to send a message
- [ ] Verify error message displayed
- [ ] Verify graceful handling (no crash)
- [ ] **Expected:** "Authentication required" error

#### Test 6.3: Empty Message Handling
- [ ] Try to send empty message
- [ ] Try to send only whitespace
- [ ] Verify messages are not sent
- [ ] Verify no error in console
- [ ] **Expected:** Silent ignore

#### Test 6.4: Long Message Handling
- [ ] Send message > 1000 characters
- [ ] Verify message displays correctly
- [ ] Verify no truncation errors
- [ ] Verify scrolling works
- [ ] **Expected:** Full message visible

---

### **PHASE 7: UI/UX Polish** ⏳

#### Test 7.1: Connection Status Indicator
- [ ] Verify green dot when connected
- [ ] Disconnect → verify red dot
- [ ] Reconnect → verify green dot returns
- [ ] **Expected:** Visual feedback

#### Test 7.2: Auto-Scroll Behavior
- [ ] Scroll to top of chat
- [ ] New message arrives
- [ ] Verify chat does NOT auto-scroll (user is reading)
- [ ] Scroll to bottom
- [ ] New message arrives
- [ ] Verify chat DOES auto-scroll
- [ ] **Expected:** Smart scroll behavior

#### Test 7.3: Input Field UX
- [ ] Focus on input field on page load
- [ ] Send message
- [ ] Verify input clears after send
- [ ] Verify focus returns to input
- [ ] **Expected:** Smooth message flow

#### Test 7.4: Timestamp Formatting
- [ ] Verify timestamps are readable
- [ ] Verify timezone handling
- [ ] Verify "Today" vs date display
- [ ] **Expected:** User-friendly format

---

## 🐛 Known Issues to Fix

### High Priority
1. [ ] **Typing indicators** - Not implemented in UI
2. [ ] **System messages** - Need distinct styling
3. [ ] **Auto-scroll** - Needs smart behavior
4. [ ] **Message input** - Not clearing after send?

### Medium Priority
5. [ ] **Timestamp formatting** - Could be more user-friendly
6. [ ] **Error messages** - Need better UI display
7. [ ] **Loading states** - Add spinners during connection

### Low Priority
8. [ ] **Emoji support** - Test and verify
9. [ ] **Link detection** - Auto-link URLs in messages
10. [ ] **Message grouping** - Group consecutive messages from same user

---

## 📊 Current Test Status

| Phase | Status | Pass Rate |
|-------|--------|-----------|
| Phase 1: Connection | ✅ Complete | 2/2 |
| Phase 2: Messages | ⏳ In Progress | 2/3 |
| Phase 3: Typing | ⏳ Pending | 0/2 |
| Phase 4: Presence | ⏳ Pending | 0/3 |
| Phase 5: Logout | ⏳ In Progress | 2/3 |
| Phase 6: Edge Cases | ⏳ Pending | 0/4 |
| Phase 7: UI/UX | ⏳ Pending | 0/4 |

**Overall:** 6/21 tests completed (29% complete)

**Additional Fixes:**
- ✅ Fixed duplicate online user counter (removed sidebar counter)
- ✅ Proper counter formatting ("X online")

---

## 🚀 Next Steps

1. ✅ **Phase 1 Complete** - Connection & Keep-Alive working
2. ⏳ **Test 2.3** - Message persistence & scrolling (optional)
3. ⏳ **Phase 3** - Typing indicators testing
4. ⏳ **Phase 4** - User presence (online/offline status)
5. ⏳ **Phase 5** - Logout functionality (CRITICAL)
6. ⏳ **Phase 6-7** - Edge cases & UI/UX polish

---

## 📝 Notes

- Server is stable after backend fixes
- Focus on one test at a time
- Document every issue found
- Test in both Chrome and Safari if possible
- Keep server terminal visible for backend logs
