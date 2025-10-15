# 📋 TODO - Socializer Project

**Date:** 2025-10-15  
**Priority System:** 🔴 Critical | 🟡 High | 🟢 Medium | 🔵 Low  

---

## ✅ COMPLETED (Current Session)

- [x] Fixed invite password bypass logic
- [x] Updated documentation (PASSWORD_PROTECTION_SUMMARY.md)
- [x] Created comprehensive test suite (test_invite_password_bypass.py)
- [x] Created development standards guide (DEVELOPMENT_STANDARDS.md)
- [x] Fixed SQLAlchemy session detachment issues
- [x] Added O-T-E logging to data_manager.py

---

## 🔴 CRITICAL - Must Do Next

### **1. Test Invite Password Bypass** 
**Status:** 🟡 Ready to Test  
**Owner:** YOU  
**Files:** `tests/test_invite_password_bypass.py`

**Action:**
```bash
# Activate venv
source .venv/bin/activate

# Run the test suite
pytest tests/test_invite_password_bypass.py -v -s

# Should see 5 tests PASS:
# ✅ test_invited_user_bypasses_password
# ✅ test_invited_user_with_wrong_password_still_succeeds  
# ✅ test_open_room_invite_still_works
# ✅ test_invalid_invite_still_fails
# ✅ test_wrong_user_accepting_invite_fails
```

**Expected Result:** All 5 tests pass  
**If Fails:** Report errors to continue debugging

---

### **2. Manual Browser Testing**
**Status:** 🟡 Ready to Test  
**Owner:** YOU  
**Depends On:** Test #1 passing

**Action:**
```bash
# Start server
uvicorn app.main:app --reload

# Open browser
# http://localhost:8000/chat
```

**Test Flow:**
1. Create two test users (User A, User B)
2. User A creates password-protected room ("secret123")
3. User A invites User B
4. User B accepts invite
5. **Expected:** No password prompt, immediate join
6. **Verify:** User B can see room in sidebar

**Success Criteria:**
- [ ] No password prompt when accepting invite
- [ ] User B added to room immediately
- [ ] Console shows: `[TRACE] User X has valid invite - bypassing password check`

---

## 🟡 HIGH PRIORITY - This Week

### **3. Add Direct Join Feature (Future)**
**Status:** 🔵 Not Started  
**Depends On:** Invite system working perfectly

**Description:**
Currently, users can only join rooms via invite. Add ability to join directly with room code/password.

**Design:**
```python
def join_room_directly(user_id: int, room_id: int, password: Optional[str]) -> bool:
    """
    Join a room without invite (direct access).
    
    PASSWORD REQUIRED for password-protected rooms!
    This is where password validation happens for uninvited users.
    """
    room = get_room(room_id)
    
    # Check password for protected rooms
    if room.password:
        if not password or password != room.password:
            print(f"[EVAL] Direct join failed: invalid password")
            return False
    
    # Add as member
    add_member(room_id, user_id)
    return True
```

**Tasks:**
- [ ] Create API endpoint: `POST /api/rooms/{id}/join`
- [ ] Add frontend "Join Room" button with room code input
- [ ] Add password prompt for protected rooms
- [ ] Write TDD tests
- [ ] Update documentation

---

### **4. Improve Test Coverage**
**Status:** 🟡 In Progress  
**Current Coverage:** ~60%  
**Target:** 80%+

**Action:**
```bash
# Check current coverage
pytest --cov=. --cov-report=html tests/

# Open report
open htmlcov/index.html
```

**Areas Needing Tests:**
- [ ] `app/routers/rooms.py` - API endpoints
- [ ] `app/routers/chat.py` - Chat endpoints
- [ ] `static/js/chat/PrivateRooms.js` - Frontend (Jest)
- [ ] WebSocket functionality
- [ ] Error handling edge cases

---

### **5. Refactor ai_chatagent.py**
**Status:** 🔵 Not Started  
**Priority:** 🟡 High  
**Blocker:** Need to complete and test rooms feature first

**From:** REFACTORING_PLAN.md

**Goal:** Extract 14 classes from 1,767-line file into modular structure

**Phase 1: Extract Tools** (1-2 days)
- [ ] Create `chat_agent/tools/` directory
- [ ] Extract `ConversationRecallTool` → `conversation_recall_tool.py`
- [ ] Extract `UserPreferenceTool` → `user_preference_tool.py`
- [ ] Extract `SkillEvaluator` → `skill_evaluator_tool.py`
- [ ] Extract `TavilySearchTool` → `tavily_search_tool.py`
- [ ] Extract `LifeEventTool` → `life_event_tool.py`
- [ ] Extract `ClarifyCommunicationTool` → `clarify_communication_tool.py`

**Phase 2: Extract Components** (1 day)
- [ ] Extract `State` → `graph/state.py`
- [ ] Extract `BasicToolNode` → `graph/tool_node.py`
- [ ] Extract `UserData` → `models/user_data.py`
- [ ] Extract `ChatSession` → `sessions/chat_session.py`

**Phase 3: Tests** (1 day)
- [ ] Write unit tests for each extracted class
- [ ] Verify all tests still pass
- [ ] Update imports throughout codebase

---

## 🟢 MEDIUM PRIORITY - Next Week

### **6. Add Room Discovery Feature**
**Status:** 🔵 Not Started

**Description:**
Allow users to browse/search for public rooms (without password).

**Features:**
- [ ] List public rooms (password=NULL)
- [ ] Search rooms by name/topic
- [ ] Show member count, activity
- [ ] Join button (no password needed for public)

---

### **7. Add Room Member Management**
**Status:** 🔵 Not Started

**Features:**
- [ ] View room members list
- [ ] Kick member (creator/admin only)
- [ ] Promote to admin
- [ ] Transfer ownership
- [ ] Ban user from room

---

### **8. Add Message History Pagination**
**Status:** 🔵 Not Started  
**Current:** Loads last 50 messages only

**Features:**
- [ ] "Load More" button
- [ ] Infinite scroll
- [ ] Jump to date
- [ ] Search messages

---

### **9. Improve Frontend UI/UX**
**Status:** 🔵 Not Started

**Tasks:**
- [ ] Add loading spinners
- [ ] Better error messages
- [ ] Toast notifications for all actions
- [ ] Keyboard shortcuts
- [ ] Dark mode support
- [ ] Mobile responsive design

---

### **10. Add Notifications System**
**Status:** 🔵 Not Started

**Features:**
- [ ] Browser notifications for new messages
- [ ] Unread message badges
- [ ] @mentions highlighting
- [ ] Email notifications (optional)

---

## 🔵 LOW PRIORITY - Future

### **11. Add Room Settings**
- [ ] Change room name
- [ ] Change room password
- [ ] Room description
- [ ] Room avatar/icon
- [ ] Notification preferences

### **12. Add Message Features**
- [ ] Edit message
- [ ] Delete message
- [ ] Reply to message
- [ ] Reactions (emoji)
- [ ] Message formatting (markdown)
- [ ] File attachments

### **13. Add AI Enhancements**
- [ ] AI can detect toxic behavior
- [ ] AI suggests ice breakers
- [ ] AI summarizes conversations
- [ ] AI translates messages

### **14. Performance Optimizations**
- [ ] Add Redis caching
- [ ] Optimize database queries
- [ ] Add database indexes
- [ ] Load balancing
- [ ] CDN for static files

### **15. Security Enhancements**
- [ ] Rate limiting
- [ ] CSRF protection
- [ ] XSS prevention audit
- [ ] SQL injection prevention audit
- [ ] Password hashing review
- [ ] API key rotation

---

## 📊 Continuous Maintenance

### **Daily/Weekly Tasks**
- [ ] Review and address console errors
- [ ] Check test coverage
- [ ] Update documentation
- [ ] Review code quality metrics
- [ ] Monitor performance

### **Code Quality Checks**
```bash
# Run all tests
pytest tests/ -v

# Check coverage
pytest --cov=. tests/

# Check for outdated dependencies
pip list --outdated

# Format code
black .

# Lint code
flake8 .
```

---

## 🎯 Next Session Goals

**When you come back, start with:**

1. ✅ **Test the invite password bypass** (Critical)
   - Run pytest suite
   - Test in browser
   - Verify console logs

2. ✅ **If tests pass:** Commit changes
   ```bash
   git add .
   git commit -m "fix: Invited users bypass password protection (TDD+O-T-E)"
   ```

3. 🔄 **Continue with:** Refactoring ai_chatagent.py (from REFACTORING_PLAN.md)

4. 📝 **Update this TODO** with progress

---

## 📝 Notes

- Always follow TDD: Test first, code second
- Always follow O-T-E: Observability, Traceability, Evaluation
- Always follow OOP: SOLID principles, one class per file
- Document as you go
- Commit small, commit often

---

**Last Updated:** 2025-10-15  
**Next Review:** After testing invite password bypass  
