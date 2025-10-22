# 🔐 Login Flow Documentation

**Current Status:** Working ✅  
**Date:** 2025-10-22  
**DO NOT MODIFY** without testing

---

## 📋 Login Flow (Step-by-Step)

### **1. User Visits Login Page**
**File:** `templates/login.html`  
**Endpoint:** `GET /login`

**What Happens:**
- Serves HTML with login form
- Loads `static/js/auth/index.js`
- Initializes LoginForm class

---

### **2. User Submits Credentials**
**File:** `static/js/auth/LoginForm.js`  
**Method:** `handleSubmit()`

**Flow:**
```javascript
1. Prevents default form submission
2. Validates username and password
3. Calls authService.login(username, password)
4. Waits 200ms for cookie to be set
5. Checks if cookie exists
6. If cookie: redirects to /chat
7. If no cookie: redirects to /chat?token=xxx (fallback)
```

---

### **3. Authentication Request**
**File:** `static/js/auth/AuthService.js`  
**Endpoint:** `POST /token`

**Request:**
```javascript
{
  username: "user",
  password: "pass"
}
```

**Response (200 OK):**
```javascript
{
  access_token: "eyJhbGciOiJIUzI1NiIs...",
  token_type: "bearer"
}
```

**What AuthService Does:**
1. Makes POST /token request
2. Receives access_token
3. Saves to localStorage as 'auth_token'
4. **Inline script in login.html intercepts and sets cookie**

---

### **4. Cookie Setting (Critical!)**
**File:** `templates/login.html` (inline script)  
**Lines:** ~40-80

**Intercepts fetch() requests:**
```javascript
// Overrides window.fetch
const originalFetch = window.fetch;
window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);
    
    // If /token request
    if (args[0].includes('/token')) {
        const data = await response.clone().json();
        
        if (data.access_token) {
            // Set cookie
            document.cookie = `access_token=Bearer ${data.access_token}; Path=/; SameSite=Lax`;
            
            // Also localStorage backup
            localStorage.setItem('auth_token', JSON.stringify(data));
        }
    }
    
    return response;
};
```

**CRITICAL:** This must run BEFORE any auth requests!

---

### **5. Redirect to Chat**
**File:** `static/js/auth/LoginForm.js`  
**Line:** ~56

**Logic:**
```javascript
// Wait for cookie
await new Promise(resolve => setTimeout(resolve, 200));

// Check cookie
const cookieSet = document.cookie.includes('access_token');

if (cookieSet) {
    // ✅ Cookie method (preferred)
    window.location.href = '/chat';
} else {
    // ⚠️ URL fallback
    window.location.href = `/chat?token=${token}`;
}
```

---

### **6. Chat Page Authentication**
**File:** `app/main.py`  
**Endpoint:** `GET /chat`  
**Lines:** ~1213-1290

**Authentication Logic:**
```python
# 1. Try URL token first
token = request.query_params.get("token")

# 2. Try cookies
if not token:
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token[7:]  # Remove 'Bearer ' prefix

# 3. Verify token
if not token:
    return RedirectResponse(url="/login")

# 4. Decode JWT
payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

# 5. Get user from DB
user = get_user_by_username(db, payload.get("sub"))

# 6. Render chat page
return templates.TemplateResponse("new-chat.html", {...})
```

---

## 🎯 Key Points

### **Why It Works:**
1. **Fetch interceptor** sets cookie immediately after /token response
2. **200ms delay** ensures cookie is available before redirect
3. **Cookie-first approach** (URL token is fallback)
4. **Backend supports both** cookie AND URL token

### **Why It Might Break:**
1. ❌ Removing fetch interceptor from login.html
2. ❌ Changing redirect timing (< 200ms)
3. ❌ Modifying cookie format (must be "Bearer {token}")
4. ❌ Browser cache preventing fetch override
5. ❌ Cookie SameSite/security settings

---

## 🔍 Debugging

### **Check Browser Console:**
```
✅ Inline cookie fix loaded
✅ Fetch interceptor installed
✅ Token received, setting cookie NOW
✅ Cookie set: access_token=Bearer eyJ...
✅ Cookie verified, redirecting to /chat
```

### **Check Server Logs:**
```
[DEBUG] Token found in URL/cookie
[DEBUG] Token length: 125 characters
[DEBUG] Successfully authenticated as user: username
```

### **If Login Fails:**
1. **Check localStorage** has 'auth_token'
2. **Check document.cookie** has 'access_token'
3. **Check redirect URL** includes token if cookie failed
4. **Clear browser cache** and try again
5. **Check console** for fetch interceptor confirmation

---

## 🚫 What NOT to Change

### **DO NOT:**
- Remove inline fetch interceptor from login.html
- Change cookie name from 'access_token'
- Change cookie format from 'Bearer {token}'
- Reduce 200ms delay
- Remove localStorage backup
- Modify redirect logic without testing

### **SAFE TO CHANGE:**
- UI/CSS of login page
- Error messages
- Button text/loading states
- Form validation messages

---

## 📝 Files Involved

| File | Purpose | Can Modify? |
|------|---------|-------------|
| templates/login.html | Login UI + fetch interceptor | ⚠️ Careful |
| static/js/auth/LoginForm.js | Form handling + redirect | ⚠️ Careful |
| static/js/auth/AuthService.js | API calls | ⚠️ Careful |
| static/js/auth/index.js | Initialization | ✅ Safe |
| app/main.py | Backend auth | ⚠️ Test thoroughly |

---

## ✅ Testing Checklist

Before deploying login changes:
- [ ] Clear browser cache (Cmd+Shift+R)
- [ ] Open DevTools console
- [ ] Login with test account
- [ ] Verify console shows fetch interceptor
- [ ] Verify cookie is set
- [ ] Verify redirect to /chat works
- [ ] Verify chat page loads (not redirected back)
- [ ] Test with both cookie AND URL token methods
- [ ] Test in incognito mode
- [ ] Test in different browser

---

**Last Verified Working:** 2025-10-22 (before Gemini tool changes)  
**Status:** ✅ WORKING - DO NOT MODIFY WITHOUT TESTING
