# Authentication Flow Documentation

## Overview
This document describes the complete authentication flow for the Socializer application, from login form submission to WebSocket chat access.

## Architecture

### Components
1. **LoginForm** (`static/js/auth/LoginForm.js`) - Handles form UI and validation
2. **AuthService** (`static/js/auth/AuthService.js`) - Manages authentication logic and token storage
3. **Backend Auth Endpoint** (`app/main.py`) - `/token` endpoint for authentication
4. **Backend User Endpoint** (`app/main.py`) - `/users/me/` endpoint for user data

## Authentication Flow

### Step 1: User Login
```
User submits login form
  ↓
LoginForm.handleSubmit() called
  ↓
event.preventDefault() - Prevents default form GET submission
  ↓
Validates username and password (client-side)
  ↓
Calls AuthService.login(username, password)
```

### Step 2: Token Request
```
AuthService.login()
  ↓
Creates URLSearchParams with:
  - username
  - password
  - grant_type: "password"
  ↓
POST to /token endpoint
  Headers:
    - Content-Type: application/x-www-form-urlencoded
    - Accept: application/json
  Credentials: include
```

### Step 3: Token Storage
```
Receives token response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
  ↓
Stores in localStorage as 'auth_token':
{
  "access_token": "...",
  "token_type": "bearer",
  "expires_in": 3600,
  "created_at": <timestamp>
}
  ↓
Sets secure cookie for WebSocket auth:
  access_token=<token>; Path=/; SameSite=Strict; Secure
```

### Step 4: User Data Retrieval
```
AuthService.getCurrentUser()
  ↓
GET to /users/me/ endpoint
  Headers:
    - Authorization: Bearer <access_token>
    - Accept: application/json
  Credentials: include
  ↓
Receives user data:
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  ...
}
  ↓
Caches in AuthService.currentUser
```

### Step 5: Redirect to Chat
```
LoginForm receives user data
  ↓
window.location.href = '/chat'
  ↓
Chat page loads with:
  - Token in localStorage
  - Token in cookie
  - User data cached
```

## WebSocket Authentication

### Connection Process
```
Chat page loads
  ↓
chat-new.js retrieves token from:
  1. localStorage.getItem('auth_token')
  2. document.cookie (access_token)
  ↓
Constructs WebSocket URL:
  ws://host/ws/chat/{room_id}?token=<access_token>
  ↓
WebSocket connects with token in query param
  ↓
Backend validates token via get_user_info()
  ↓
Connection established and user can send/receive messages
```

## Security Considerations

### Token Storage
- **localStorage**: Primary storage, accessible by JavaScript
- **Secure Cookie**: For WebSocket authentication, HttpOnly flag set by backend
- **SameSite=Strict**: Prevents CSRF attacks
- **Secure flag**: Ensures transmission over HTTPS only

### Token Validation
- Backend validates token on every WebSocket connection
- Token expiration checked (expires_in)
- Inactive users rejected

### Error Handling
- Invalid credentials: Clear error message
- Network errors: Retry logic
- Expired tokens: Automatic refresh (if refresh token available)
- Authentication failures: Clear stored data and redirect to login

## Common Issues and Solutions

### Issue: Form submits as GET request
**Cause**: Multiple event handlers or missing preventDefault()
**Solution**: Ensure only one event handler and call event.preventDefault() first

### Issue: POST to wrong endpoint
**Cause**: Incorrect baseUrl in AuthService
**Solution**: Set baseUrl to '' for root-level endpoints

### Issue: WebSocket connection fails
**Cause**: Token not accessible or expired
**Solution**: Check localStorage and cookie, ensure token is valid

### Issue: 401 Unauthorized
**Cause**: Invalid or expired token
**Solution**: Clear auth data and redirect to login

## Testing Checklist

### Manual Testing
- [ ] Fill login form with valid credentials
- [ ] Verify POST request to /token (not GET)
- [ ] Check token stored in localStorage
- [ ] Verify cookie set with access_token
- [ ] Confirm redirect to /chat
- [ ] Test WebSocket connection establishes
- [ ] Send and receive chat messages

### Browser Console Checks
```javascript
// Check token storage
console.log(localStorage.getItem('auth_token'));

// Check cookie
console.log(document.cookie);

// Check AuthService
console.log(window.authService.isAuthenticated());
console.log(window.authService.getToken());
```

### Network Tab Verification
1. Login request: POST /token (not GET /login)
2. User data request: GET /users/me/
3. WebSocket upgrade: ws://host/ws/chat/{room_id}

## Code Standards

### JavaScript (ESLint/Prettier)
- Use async/await for asynchronous operations
- Proper error handling with try/catch
- Clear variable and function names
- JSDoc comments for all public methods
- Use const/let, not var

### Python (PEP 8)
- 4 spaces for indentation
- Max line length: 79 characters
- Docstrings for all functions/classes
- Type hints where applicable
- Clear error messages

## Future Improvements

1. **Token Refresh**: Implement automatic token refresh before expiration
2. **Remember Me**: Option to extend session duration
3. **Multi-factor Authentication**: Add 2FA support
4. **Session Management**: Allow users to view/revoke active sessions
5. **Rate Limiting**: Prevent brute force login attempts
