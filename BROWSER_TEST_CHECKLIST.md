# 🧪 Browser Testing Checklist

## Pre-Test Setup
- [x] Server running on http://127.0.0.1:8000
- [x] All automated tests passed (3/3)
- [ ] Browser opened to chat page

---

## Test 1: Initial State ✅
**URL:** http://127.0.0.1:8000/chat

**Check:**
- [ ] Page loads without errors
- [ ] "AI Off" button visible in send controls
- [ ] "Ask AI" button visible
- [ ] Input placeholder says "Type your message... (use /ai for AI assistant)"
- [ ] No JavaScript errors in console (F12)

---

## Test 2: AI Toggle ✅
**Action:** Click the "AI Off" button

**Expected:**
- [ ] Button changes to "AI On"
- [ ] Button background changes to purple gradient
- [ ] Blue info message appears: "🤖 AI Assistant activated!"
- [ ] State saved (check localStorage: `aiAssistantEnabled: true`)

**Action:** Refresh page

**Expected:**
- [ ] AI button still shows "AI On"
- [ ] State persists after reload

---

## Test 3: /ai Command ✅
**Action:** Type `/ai Hello! Introduce yourself` and press Enter

**Expected:**
- [ ] Input clears
- [ ] Green typing indicator appears (3 bouncing dots)
- [ ] Typing indicator disappears after ~2-3 seconds
- [ ] AI response appears in green gradient box
- [ ] Response starts with "🤖 AI Assistant:"
- [ ] Response mentions "Social Coach" or "Communication Assistant"
- [ ] No raw JSON visible

---

## Test 4: Weather Query ✅
**Action:** Type `/ai What's the weather in Tokyo?`

**Expected:**
- [ ] Typing indicator appears
- [ ] Response includes temperature (e.g., "22.2°C")
- [ ] Response formatted nicely (not raw JSON)
- [ ] Tools indicator shows "🔧 Tools: tavily_search"
- [ ] Response in green AI message box

---

## Test 5: Ask AI Button ✅
**Action:** Click "Ask AI" button

**Expected:**
- [ ] Input field auto-fills with `/ai `
- [ ] Cursor positioned after `/ai ` for typing
- [ ] Can type question immediately

**Action:** Type `What time is it?` and press Enter

**Expected:**
- [ ] AI responds with time information
- [ ] Green AI message box
- [ ] No errors

---

## Test 6: Error Handling ✅
**Action:** Type `/ai` (without question) and press Enter

**Expected:**
- [ ] Blue info message: "Please provide a question after /ai..."
- [ ] No typing indicator
- [ ] No API call made

---

## Test 7: Normal Chat ✅
**Action:** Type a regular message (without `/ai`)

**Expected:**
- [ ] Message sends normally to chat
- [ ] Does NOT trigger AI
- [ ] Message appears in WebSocket chat
- [ ] Other users can see it

---

## Test 8: Mobile Responsive ✅
**Action:** Resize browser to mobile width (< 768px)

**Expected:**
- [ ] AI buttons still visible
- [ ] Buttons properly sized for mobile
- [ ] AI messages readable
- [ ] No overflow issues

---

## Test 9: Rapid Fire ✅
**Action:** Send multiple `/ai` commands quickly

**Expected:**
- [ ] Each command processed separately
- [ ] No duplicate responses
- [ ] Typing indicators don't stack
- [ ] Responses appear in order

---

## Test 10: Toggle Off ✅
**Action:** Click "AI On" button to toggle off

**Expected:**
- [ ] Button changes to "AI Off"
- [ ] Button returns to gray color
- [ ] Info message: "AI Assistant deactivated"
- [ ] `/ai` commands still work (not disabled, just preference saved)

---

## Browser Compatibility
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

---

## Console Checks (F12 → Console)
**Look for:**
- [ ] No red errors
- [ ] AI toggle/button logs appear
- [ ] "🤖 AI command detected" when using `/ai`
- [ ] API responses successful (200 status)

**Network Tab:**
- [ ] POST to `/api/ai-chat` returns 200
- [ ] Response time < 10 seconds
- [ ] Proper Authorization header

---

## Final Verification ✅

### Functionality
- [ ] AI toggle works (on/off)
- [ ] `/ai` command detected and processed
- [ ] "Ask AI" button inserts `/ai `
- [ ] Typing indicators animate smoothly
- [ ] AI responses formatted beautifully
- [ ] Tools display when used
- [ ] State persists across reloads
- [ ] Error messages clear and helpful

### UI/UX
- [ ] All buttons styled correctly
- [ ] Colors match design (purple for AI, green for messages)
- [ ] Animations smooth (no jank)
- [ ] Text readable and properly sized
- [ ] Icons display correctly (🤖, ⭐, 🔧)
- [ ] Responsive on all screen sizes

### Performance
- [ ] No memory leaks (check with multiple commands)
- [ ] Smooth scrolling to new messages
- [ ] No lag when toggling AI
- [ ] Fast response times (< 5s average)

---

## Known Issues / Notes

**Write any issues found here:**

```
Example:
- [ ] Issue: Typing indicator doesn't disappear on timeout
- [ ] Issue: Button text overlaps on very small screens
- [ ] Issue: AI responses too wide on mobile
```

---

## Sign-Off

**Tested By:** _________________  
**Date:** October 8, 2025  
**Browser:** _________________  
**Status:** ⬜ Pass ⬜ Fail ⬜ Needs Work  

**Notes:**
