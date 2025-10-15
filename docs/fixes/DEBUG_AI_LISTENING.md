# 🔍 Debug Guide: AI Passive Listening

**Created:** October 8, 2025, 11:41 AM  
**Purpose:** Debug translation detection and suggestion clicking

---

## 🎯 What We Fixed

### 1. Added Extensive Console Logging
Every step now logs to console so we can see exactly what's happening.

### 2. Improved Click Handling
- Added `e.preventDefault()` and `e.stopPropagation()`
- Added event capture mode
- Added try-catch for error handling
- Added keyboard support (Enter/Space)

### 3. Enhanced Translation Detection
- Lowered foreign language threshold: 10 chars → **5 chars**
- More lenient keyword matching (removed word boundaries where needed)
- Better detection logging

### 4. Visual Improvements
- Thicker border (3px)
- Better hover effects
- Active state feedback
- Box shadow for depth

---

## 🧪 Testing Steps

### Step 1: Open Browser Console
1. Open http://127.0.0.1:8000/chat
2. Press **F12** (or Cmd+Option+I on Mac)
3. Click **Console** tab
4. Keep it visible while testing

### Step 2: Toggle AI On
1. Click "AI Off" button
2. **Look for in console:**
   ```
   [AI] Starting passive listening...
   [AI] Passive listening active
   ```
3. **Check:**
   - Button turns purple ✅
   - Text changes to "AI On" ✅
   - "Listening..." indicator appears ✅

---

## 📊 Console Output Guide

### When AI is Toggled On:
```javascript
[AI] Starting passive listening...
[AI] Passive listening active
```

### When You Type (each keystroke):
```javascript
[AI] Input changed: "h"
[AI] Input changed: "he"
[AI] Input changed: "hel"
[AI] Input changed: "help"
```

### When You Stop Typing (after 2 seconds):
```javascript
[AI] Analyzing text for suggestions: "help me please"
[AI] Detection results: {
  isQuestion: false,
  hasHelpKeywords: true,
  hasTranslateKeywords: false,
  hasNonAscii: false,
  likelyForeignLanguage: false,
  textLength: 15
}
[AI] Creating suggestion!
[AI] Suggestion element created
[AI] ✅ Suggestion added to DOM and visible
```

### When You Click Suggestion:
```javascript
[AI] ✅ Suggestion clicked! Captured text: "help me please"
[AI] Sending to handleAICommand...
[AI] Command sent successfully
[AI] Input cleared
[AI] Suggestion removed
```

---

## 🐛 Troubleshooting

### Problem 1: No Console Logs When Typing

**Symptoms:**
- You type but see no `[AI] Input changed:` logs

**Causes:**
1. AI is not toggled on
2. Passive listening not started

**Solution:**
```javascript
// Check in console:
isAIActive  // Should be: true
isListening // Should be: true

// Manually restart:
startPassiveListening()
```

---

### Problem 2: Detection Results All False

**Example Console:**
```javascript
[AI] Detection results: {
  isQuestion: false,
  hasHelpKeywords: false,
  hasTranslateKeywords: false,
  hasNonAscii: false,
  likelyForeignLanguage: false
}
[AI] ❌ No trigger matched - no suggestion created
```

**This means:**
- Text doesn't end with `?`
- No help keywords detected
- No translation keywords detected
- No foreign characters detected

**Test with these guaranteed triggers:**

1. **Question:**
   ```
   Type: "Hello there?"
   Should detect: isQuestion: true
   ```

2. **Help keywords:**
   ```
   Type: "can you help me"
   Should detect: hasHelpKeywords: true
   ```

3. **Translation keywords:**
   ```
   Type: "what does hello mean"
   Should detect: hasTranslateKeywords: true
   ```

4. **Foreign language:**
   ```
   Type: "Bonjour"
   Should detect: hasNonAscii: true
   ```

---

### Problem 3: Rate Limited

**Console Shows:**
```javascript
[AI] Rate limited, wait: 25 seconds
```

**This is normal!** Max 1 suggestion per 30 seconds.

**To reset:**
```javascript
// In console, run:
lastSuggestedHelp = 0
```

---

### Problem 4: Suggestion Not Clickable

**Checklist:**
1. Can you see the suggestion? ✅
2. Does cursor change to pointer on hover? ✅
3. Does it scale up on hover? ✅
4. When you click, do you see console logs? ❌

**If no console logs when clicking:**

Try clicking again and check:
```javascript
// Should see:
[AI] ✅ Suggestion clicked!
```

**If still nothing:**
1. Inspect element in DevTools
2. Check if click handler is attached
3. Try pressing Enter key while suggestion is focused

---

### Problem 5: Translation Not Detected

**Test these specific phrases:**

```javascript
// 1. Direct keyword
"translate this" 
// Should trigger: hasTranslateKeywords: true

// 2. Question pattern  
"what does bonjour mean"
// Should trigger: hasTranslateKeywords: true

// 3. Foreign text
"Bonjour comment allez-vous"
// Should trigger: likelyForeignLanguage: true

// 4. Mixed
"how do you say hello in Spanish"
// Should trigger: hasTranslateKeywords: true
```

---

## 📝 Debug Commands

### Check Status:
```javascript
// In browser console:
console.log({
    isAIActive,
    isListening,
    lastSuggestedHelp: new Date(lastSuggestedHelp).toLocaleTimeString()
})
```

### Manually Trigger Test:
```javascript
// Create a fake suggestion manually:
const input = document.getElementById('message-input');
input.value = "How do you say hello in French?";
input.dispatchEvent(new Event('input'));
```

### Reset Rate Limit:
```javascript
lastSuggestedHelp = 0;
console.log('Rate limit reset');
```

### Force Suggestion:
```javascript
// This will show a test suggestion:
handlePassiveListening({ 
    target: { value: "How are you?" } 
});
```

---

## 🎯 Expected Behavior

### Test 1: Simple Question
```
Input: "How are you?"
Wait: 2 seconds
✅ Should see:
  - [AI] Analyzing text...
  - isQuestion: true
  - [AI] Creating suggestion!
  - Suggestion appears
  - Click works
```

### Test 2: Translation Request
```
Input: "translate hello to French"
Wait: 2 seconds
✅ Should see:
  - hasTranslateKeywords: true
  - 🌐 icon in suggestion
  - "Need help with translation?"
  - Click works
```

### Test 3: Foreign Language
```
Input: "Bonjour"
Wait: 2 seconds
✅ Should see:
  - hasNonAscii: true
  - likelyForeignLanguage: true
  - 🌐 icon
  - Click works
```

---

## 🔧 Manual Fix (If Nothing Works)

### Hard Reset:
```javascript
// In console:
stopPassiveListening();
isAIActive = false;
isListening = false;

// Then toggle AI off and on again in UI
```

### Verify Event Listener:
```javascript
// Check if listener is attached:
const input = document.getElementById('message-input');
console.log('Event listeners:', getEventListeners(input));
// Should show 'input' event with handlePassiveListening
```

---

## ✅ Success Criteria

You'll know it's working when:

1. **Typing shows logs:**
   ```
   [AI] Input changed: "..."
   ```

2. **After 2 seconds:**
   ```
   [AI] Analyzing text...
   [AI] Detection results: {...}
   ```

3. **Suggestion appears:**
   ```
   [AI] Creating suggestion!
   [AI] ✅ Suggestion added to DOM
   ```

4. **Click works:**
   ```
   [AI] ✅ Suggestion clicked!
   [AI] Command sent successfully
   ```

---

## 🆘 Still Not Working?

### Share These Details:

1. **Console output** (copy all `[AI]` logs)
2. **What you typed**
3. **What you expected**
4. **What actually happened**
5. **Browser** (Chrome, Firefox, Safari)
6. **Any errors** (red messages in console)

### Quick Checklist:

- [ ] Browser console open (F12)
- [ ] AI toggled ON (purple button)
- [ ] "Listening..." indicator visible
- [ ] Typed text and waited 2 seconds
- [ ] Saw `[AI]` logs in console
- [ ] Detection results logged
- [ ] Suggestion appeared
- [ ] Clicked suggestion
- [ ] Saw click logs

---

## 📸 What You Should See

### Console Output Example:
```
[AI] Starting passive listening...
[AI] Passive listening active
[AI] Input changed: "How do you say hello"
[AI] Analyzing text for suggestions: How do you say hello
[AI] Detection results: {
  isQuestion: false,
  hasHelpKeywords: true,
  hasTranslateKeywords: true,
  hasNonAscii: false,
  likelyForeignLanguage: false,
  textLength: 21
}
[AI] Creating suggestion!
[AI] Suggestion element created
[AI] ✅ Suggestion added to DOM and visible
```

### Then when you click:
```
[AI] ✅ Suggestion clicked! Captured text: How do you say hello
[AI] Sending to handleAICommand...
[AI] Command sent successfully
[AI] Input cleared
[AI] Suggestion removed
```

---

**Ready to test!** Open the browser console and start typing! 🚀
