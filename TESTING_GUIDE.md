# 🧪 AI Agent Testing Guide

**Date:** October 7, 2025  
**Goal:** Comprehensive testing of AI Social Coach integration

---

## 🎯 **Testing Objectives**

1. ✅ Verify AI agent responds correctly
2. ✅ Test web search functionality (weather, current events)
3. ✅ Validate memory recall (20 messages context)
4. ✅ Confirm social behavior training responses
5. ✅ Test error handling
6. ✅ Verify response formatting (beautiful output)

---

## 🚀 **Prerequisites**

### **1. Server Running:**
```bash
cd /Users/leeroystevenson/PycharmProjects/Socializer
source .venv/bin/activate
uvicorn app.main:app --reload
```

### **2. User Account:**
- Username: `human`
- Password: `FuckShit123.`

### **3. API Keys Set:**
```bash
# Check .env file has:
OPENAI_API_KEY=your_key
TAVILY_API_KEY=your_key
```

---

## 📝 **Test Suite**

### **TEST 1: Basic Functionality** ✅
**Goal:** Verify AI agent responds to basic queries

**Test Cases:**
1. **Introduction:**
   - Input: `Hello! Can you introduce yourself?`
   - Expected: AI introduces itself as Social Coach
   - Success Criteria: Response mentions social training, communication

2. **Simple Question:**
   - Input: `What are 3 tips for better communication?`
   - Expected: Structured list with 3 tips
   - Success Criteria: Clear, actionable advice

**How to Test:**
- Visit: http://127.0.0.1:8000/login
- Login with credentials above
- Visit: http://127.0.0.1:8000/test-ai
- Click "Test 1: Introduction" button
- Verify response is conversational and helpful

---

### **TEST 2: Web Search & Weather** 🌤️
**Goal:** Verify Tavily search integration works

**Test Cases:**
1. **Weather Query:**
   - Input: `What's the weather in Tokyo right now?`
   - Expected: Formatted weather report with emoji 🌤️
   - Success Criteria: 
     - Shows temperature in C° and F°
     - Shows humidity, wind
     - No raw JSON visible
     - Beautiful formatting

2. **Current Events:**
   - Input: `What are the latest news about AI?`
   - Expected: Web search results
   - Success Criteria:
     - Shows 1-3 relevant results
     - Includes sources
     - No errors

3. **General Knowledge:**
   - Input: `Who won the latest Nobel Prize in Physics?`
   - Expected: Web search with answer
   - Success Criteria: Current, accurate information

**How to Test:**
- In test-ai page, click "Test 2: Weather Query"
- Or type custom weather query
- Verify beautiful formatting (not raw JSON)

---

### **TEST 3: Memory & Context** 💭
**Goal:** Verify 20-message memory and context awareness

**Test Cases:**
1. **Store Information:**
   - Input: `My favorite color is purple`
   - Expected: AI acknowledges and confirms
   - Follow-up: `What's my favorite color?`
   - Expected: AI recalls "purple"

2. **Conversation Context:**
   - Input: `I live in Berlin`
   - Follow-up: `What's the weather where I live?`
   - Expected: AI searches weather for Berlin
   - Success Criteria: Uses context from previous message

3. **Long Conversation:**
   - Have a 10-message conversation
   - Ask: `What did we talk about earlier?`
   - Expected: AI summarizes previous topics
   - Success Criteria: Recalls topics from earlier messages

**How to Test:**
- Have a conversation with multiple messages
- Test recall with questions about earlier topics
- Verify AI remembers details

---

### **TEST 4: Social Behavior Training** 🎓
**Goal:** Verify AI provides social coaching

**Test Cases:**
1. **Rude Language:**
   - Input: `I told my boss "gimme that report now"`
   - Expected: AI gently suggests more polite alternatives
   - Success Criteria:
     - Points out issue
     - Provides better alternatives
     - Explains why (educational)
     - Non-judgmental tone

2. **Positive Behavior:**
   - Input: `I said "please" and "thank you" to everyone today`
   - Expected: AI praises positive behavior
   - Success Criteria: Encouragement and reinforcement

3. **Communication Advice:**
   - Input: `How should I ask my roommate to be quieter?`
   - Expected: Structured advice on polite communication
   - Success Criteria: Empathetic, practical suggestions

**How to Test:**
- Type scenarios involving social situations
- Verify AI provides constructive feedback
- Check tone is supportive, not preachy

---

### **TEST 5: Translation Support** 🌍
**Goal:** Verify translation capabilities

**Test Cases:**
1. **Direct Translation:**
   - Input: `Translate "Hello, how are you?" to Spanish`
   - Expected: Translation provided
   - Success Criteria: Correct translation

2. **Language Detection:**
   - Input: `Hola, ¿cómo estás?`
   - Expected: AI detects Spanish, offers to translate or practice
   - Success Criteria: Appropriate response

**How to Test:**
- Request translations
- Test with different languages
- Verify AI offers help appropriately

---

### **TEST 6: Error Handling** ⚠️
**Goal:** Verify graceful error handling

**Test Cases:**
1. **Rate Limit:**
   - Make 5+ rapid requests
   - Expected: Automatic retry after delay
   - Success Criteria: No crash, eventual response

2. **Invalid Query:**
   - Input: Random gibberish
   - Expected: AI asks for clarification
   - Success Criteria: Helpful, not error message

3. **Network Error:**
   - Disconnect internet briefly
   - Input: Weather query
   - Expected: Helpful error message
   - Success Criteria: "Connection error" not technical trace

**How to Test:**
- Intentionally trigger edge cases
- Verify errors are user-friendly

---

### **TEST 7: Response Formatting** 🎨
**Goal:** Verify beautiful output (no raw JSON)

**Test Cases:**
1. **Weather Format:**
   - Should see: `🌤️ **Temperature:** 22°C`
   - Should NOT see: `{'temp_c': 22, 'humidity': 78}`

2. **Search Results:**
   - Should see: `📚 **Search Results:**`
   - Should NOT see: Raw API responses

3. **Memory Recall:**
   - Should see: `💬 **Previous Conversation:**`
   - Should NOT see: JSON arrays

**How to Test:**
- Check every response for formatting
- Ensure no raw JSON visible
- Verify emojis and markdown work

---

## 📊 **Testing Checklist**

### **Basic Functionality:**
- [ ] AI responds to greetings
- [ ] AI provides communication tips
- [ ] Responses are conversational
- [ ] No crashes or errors

### **Web Search:**
- [ ] Weather queries work
- [ ] Current events searchable
- [ ] Results formatted beautifully
- [ ] No raw JSON visible

### **Memory:**
- [ ] AI remembers user details
- [ ] Recalls previous topics
- [ ] Uses context appropriately
- [ ] 20-message history loaded

### **Social Training:**
- [ ] Provides polite alternatives
- [ ] Explains reasoning
- [ ] Praises good behavior
- [ ] Non-judgmental tone

### **Translation:**
- [ ] Translates on request
- [ ] Detects languages
- [ ] Offers appropriate help

### **Error Handling:**
- [ ] Rate limits handled
- [ ] User-friendly errors
- [ ] No technical traces shown
- [ ] Graceful degradation

### **Formatting:**
- [ ] Weather: Beautiful format
- [ ] Search: Clean results
- [ ] Memory: Organized display
- [ ] Emojis working
- [ ] Markdown rendering

---

## 🐛 **If Issues Found**

### **Problem: AI not responding**
**Check:**
1. Server running?
2. API keys set in .env?
3. User logged in?
4. Check browser console for errors

### **Problem: Raw JSON showing**
**Check:**
1. Response formatter imported?
2. Check server logs for errors
3. Verify formatter is being called

### **Problem: Memory not working**
**Check:**
1. Database file exists?
2. Messages being saved?
3. User ID correct?

### **Problem: Web search failing**
**Check:**
1. TAVILY_API_KEY set?
2. Internet connection?
3. Rate limits hit?

---

## ✅ **Success Criteria**

Test is successful when:
- ✅ All 7 test categories pass
- ✅ No raw JSON visible to users
- ✅ Responses are helpful and conversational
- ✅ Errors are user-friendly
- ✅ Memory recall works
- ✅ Web search functional
- ✅ Social training effective

---

## 📝 **Test Results Template**

```
TEST SESSION: [Date/Time]
TESTER: [Your Name]

TEST 1 - Basic Functionality: [ PASS / FAIL ]
Notes: _________________________

TEST 2 - Web Search: [ PASS / FAIL ]
Notes: _________________________

TEST 3 - Memory: [ PASS / FAIL ]
Notes: _________________________

TEST 4 - Social Training: [ PASS / FAIL ]
Notes: _________________________

TEST 5 - Translation: [ PASS / FAIL ]
Notes: _________________________

TEST 6 - Error Handling: [ PASS / FAIL ]
Notes: _________________________

TEST 7 - Formatting: [ PASS / FAIL ]
Notes: _________________________

OVERALL: [ PASS / FAIL ]
```

---

## 🚀 **Next Steps After Testing**

**If All Tests Pass:**
→ Proceed to Phase 3: Frontend Integration

**If Issues Found:**
→ Document issues
→ Create bug fixes
→ Re-test

---

**Happy Testing!** 🎉
