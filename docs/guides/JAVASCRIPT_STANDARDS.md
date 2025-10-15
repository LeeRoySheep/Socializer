# JavaScript Coding Standards

**Socializer Project**  
**Version:** 1.0  
**Last Updated:** 2025-10-15

---

## 📋 **Table of Contents**

1. [Code Style](#code-style)
2. [Documentation (JSDoc)](#documentation-jsdoc)
3. [O-T-E Standards](#ote-standards)
4. [Module Structure](#module-structure)
5. [Error Handling](#error-handling)
6. [Testing Requirements](#testing-requirements)
7. [Security Best Practices](#security-best-practices)

---

## 🎨 **Code Style**

### **General Rules**

```javascript
// ✅ DO: Use const for values that don't change
const MAX_RETRY_ATTEMPTS = 5;
const config = { timeout: 3000 };

// ✅ DO: Use let for values that change
let retryCount = 0;
let isConnected = false;

// ❌ DON'T: Use var (legacy, function-scoped)
var oldStyle = 'avoid';

// ✅ DO: Use arrow functions for callbacks
items.map(item => item.value);
items.filter(item => item.active);

// ✅ DO: Use descriptive names
const authenticatedUser = getCurrentUser();
const isValidToken = validateToken(token);

// ❌ DON'T: Use single-letter or cryptic names
const x = getU();  // What is x? What is getU?
```

### **Naming Conventions**

```javascript
// Classes: PascalCase
class WebSocketService {}
class ChatController {}

// Functions/Methods: camelCase
function sendMessage() {}
function getUserProfile() {}

// Constants: UPPER_SNAKE_CASE
const MAX_MESSAGE_LENGTH = 1000;
const API_BASE_URL = 'https://api.example.com';

// Private methods: _prefixed camelCase
class MyClass {
    _privateMethod() {}
    publicMethod() {}
}

// Boolean variables: is/has/should prefix
const isActive = true;
const hasPermission = false;
const shouldRetry = true;
```

### **File Organization**

```javascript
/**
 * 1. File-level documentation
 * 2. Imports
 * 3. Constants
 * 4. Class/Function definitions
 * 5. Exports
 */

/**
 * ChatService - Handles chat message operations
 */

// Imports
import { WebSocketService } from './WebSocketService.js';
import { AuthService } from '../auth/AuthService.js';

// Constants
const MESSAGE_TYPES = {
    CHAT: 'chat_message',
    SYSTEM: 'system_message',
    ERROR: 'error_message'
};

// Class definition
class ChatService {
    // ... implementation
}

// Export
export { ChatService };
```

---

## 📝 **Documentation (JSDoc)**

### **File-Level Documentation**

```javascript
/**
 * WebSocketService - Robust WebSocket connection manager
 * 
 * Provides automatic reconnection, ping-pong health checks,
 * and comprehensive event handling for real-time communication.
 * 
 * @module WebSocketService
 * @requires WebSocket
 * @version 1.0.0
 * @author Socializer Team
 * 
 * @example
 * ```javascript
 * const ws = new WebSocketService('ws://localhost:8000/ws');
 * ws.on('message', handleMessage);
 * ws.connect();
 * ```
 */
```

### **Class Documentation**

```javascript
/**
 * ChatController manages chat message flow and UI updates.
 * 
 * Coordinates between WebSocket service, UI components, and
 * message persistence layer.
 * 
 * @class
 * @param {WebSocketService} wsService - WebSocket connection handler
 * @param {HTMLElement} container - DOM element for chat UI
 * @param {Object} options - Configuration options
 * @param {number} [options.maxMessages=100] - Max messages to display
 * @param {boolean} [options.autoScroll=true] - Auto-scroll to new messages
 * 
 * @property {WebSocketService} wsService - WebSocket instance
 * @property {HTMLElement} container - Chat container element
 * @property {Array<Message>} messages - Message history
 * @property {boolean} isConnected - Connection status
 * 
 * @fires ChatController#message
 * @fires ChatController#error
 * @fires ChatController#connected
 * 
 * @example
 * ```javascript
 * const controller = new ChatController(wsService, document.getElementById('chat'), {
 *     maxMessages: 50,
 *     autoScroll: true
 * });
 * 
 * controller.on('message', (msg) => console.log('New message:', msg));
 * controller.connect();
 * ```
 */
class ChatController {
    constructor(wsService, container, options = {}) {
        // ...
    }
}
```

### **Method Documentation**

```javascript
/**
 * Send a chat message to the server.
 * 
 * Validates message content, adds metadata, and sends via WebSocket.
 * Automatically retries on failure if connection is restored.
 * 
 * @async
 * @param {string} content - Message text content (max 1000 chars)
 * @param {Object} [options] - Additional message options
 * @param {string} [options.roomId] - Target room ID (default: 'general')
 * @param {boolean} [options.isPrivate=false] - Mark as private message
 * 
 * @returns {Promise<Message>} Resolves with sent message object
 * 
 * @throws {ValidationError} If content is empty or too long
 * @throws {ConnectionError} If WebSocket is not connected
 * @throws {RateLimitError} If rate limit is exceeded
 * 
 * @fires ChatController#messageSent
 * 
 * @example
 * ```javascript
 * try {
 *     const message = await controller.sendMessage('Hello!', {
 *         roomId: 'room_42',
 *         isPrivate: false
 *     });
 *     console.log('Message sent:', message.id);
 * } catch (error) {
 *     console.error('Send failed:', error);
 * }
 * ```
 */
async sendMessage(content, options = {}) {
    // Validation
    if (!content || content.trim().length === 0) {
        throw new ValidationError('Message content cannot be empty');
    }
    
    if (content.length > 1000) {
        throw new ValidationError('Message exceeds maximum length');
    }
    
    // ... implementation
}
```

### **Event Documentation**

```javascript
/**
 * Message event - Fired when a new message is received
 * 
 * @event ChatController#message
 * @type {Object}
 * @property {string} id - Unique message ID
 * @property {string} content - Message text
 * @property {string} senderId - User ID of sender
 * @property {string} senderName - Display name of sender
 * @property {number} timestamp - Unix timestamp (ms)
 * @property {string} roomId - Room where message was sent
 */
```

---

## 🔍 **O-T-E Standards**

### **OBSERVABILITY - Logging & Monitoring**

```javascript
/**
 * UserAuthentication service
 * 
 * OBSERVABILITY:
 * - Logs all authentication attempts (success/failure)
 * - Tracks token refresh operations
 * - Monitors session duration
 * - Records logout events
 * - Emits metrics for authentication latency
 */
class UserAuthentication {
    async login(username, password) {
        console.log(`[Auth] Login attempt for user: ${username}`);
        const startTime = Date.now();
        
        try {
            const result = await this._authenticateUser(username, password);
            const duration = Date.now() - startTime;
            
            console.log(`[Auth] Login successful for ${username} (${duration}ms)`);
            this._emitMetric('auth.login.success', { duration, username });
            
            return result;
        } catch (error) {
            console.error(`[Auth] Login failed for ${username}:`, error.message);
            this._emitMetric('auth.login.failure', { username, error: error.message });
            throw error;
        }
    }
}
```

### **TRACEABILITY - Event Tracking**

```javascript
/**
 * MessageQueue service
 * 
 * TRACEABILITY:
 * - Assigns unique ID to each message
 * - Timestamps all operations
 * - Tracks message lifecycle (created → sent → delivered → read)
 * - Associates messages with user sessions
 * - Maintains audit trail for sensitive operations
 */
class MessageQueue {
    addMessage(content, metadata = {}) {
        const message = {
            id: this._generateUniqueId(),
            content,
            userId: metadata.userId,
            sessionId: this._getSessionId(),
            timestamp: Date.now(),
            status: 'created',
            trace: {
                created: Date.now(),
                createdBy: metadata.userId,
                source: 'web_client'
            }
        };
        
        console.log(`[MessageQueue] Message created: ${message.id} by user ${message.userId}`);
        this.queue.push(message);
        
        return message;
    }
}
```

### **EVALUATION - Validation & Security**

```javascript
/**
 * InputValidator service
 * 
 * EVALUATION:
 * - Validates all user inputs before processing
 * - Sanitizes HTML/XSS attempts
 * - Enforces rate limits per user
 * - Checks authentication status
 * - Verifies permissions for sensitive operations
 */
class InputValidator {
    /**
     * Validate and sanitize message content
     * 
     * @param {string} content - Raw message content
     * @returns {string} Sanitized content
     * @throws {ValidationError} If content is invalid
     */
    validateMessage(content) {
        // Check empty
        if (!content || content.trim().length === 0) {
            throw new ValidationError('Message cannot be empty');
        }
        
        // Check length
        if (content.length > this.MAX_LENGTH) {
            throw new ValidationError(`Message exceeds ${this.MAX_LENGTH} characters`);
        }
        
        // Sanitize HTML
        const sanitized = this._sanitizeHTML(content);
        
        // Check for spam patterns
        if (this._isSpam(sanitized)) {
            throw new ValidationError('Message appears to be spam');
        }
        
        console.log(`[Validator] Message validated successfully`);
        return sanitized;
    }
}
```

---

## 🏗️ **Module Structure**

### **ES6 Module Pattern**

```javascript
/**
 * AuthService.js - Authentication service module
 */

// Imports at top
import { API } from './api.js';
import { StorageService } from './storage.js';

// Constants
const TOKEN_KEY = 'auth_token';
const TOKEN_EXPIRY_KEY = 'token_expiry';

// Main class/service
class AuthService {
    constructor() {
        this.storage = new StorageService();
        this.token = null;
    }
    
    // Public methods
    async login(username, password) {
        // ...
    }
    
    async logout() {
        // ...
    }
    
    isAuthenticated() {
        // ...
    }
    
    // Private methods
    _storeToken(token) {
        // ...
    }
    
    _clearToken() {
        // ...
    }
}

// Single export
export { AuthService };

// Or default export
// export default AuthService;
```

### **Singleton Pattern**

```javascript
/**
 * AuthService singleton instance
 */
class AuthService {
    constructor() {
        if (AuthService.instance) {
            return AuthService.instance;
        }
        
        this.token = null;
        AuthService.instance = this;
    }
    
    // Methods...
}

// Export singleton instance
export const authService = new AuthService();
```

---

## ⚠️ **Error Handling**

### **Custom Error Classes**

```javascript
/**
 * Custom error classes for better error handling
 */

class AppError extends Error {
    constructor(message, code, statusCode = 500) {
        super(message);
        this.name = this.constructor.name;
        this.code = code;
        this.statusCode = statusCode;
        this.timestamp = Date.now();
        Error.captureStackTrace(this, this.constructor);
    }
}

class ValidationError extends AppError {
    constructor(message) {
        super(message, 'VALIDATION_ERROR', 400);
    }
}

class AuthenticationError extends AppError {
    constructor(message) {
        super(message, 'AUTH_ERROR', 401);
    }
}

class ConnectionError extends AppError {
    constructor(message) {
        super(message, 'CONNECTION_ERROR', 503);
    }
}

// Usage
throw new ValidationError('Email format is invalid');
throw new AuthenticationError('Invalid credentials');
throw new ConnectionError('Failed to connect to server');
```

### **Try-Catch Best Practices**

```javascript
// ✅ DO: Catch specific errors, log with context
async function sendMessage(content) {
    try {
        const validated = this.validator.validate(content);
        const result = await this.api.send(validated);
        console.log('[Chat] Message sent successfully:', result.id);
        return result;
    } catch (error) {
        if (error instanceof ValidationError) {
            console.warn('[Chat] Validation failed:', error.message);
            this.ui.showError('Please check your message content');
        } else if (error instanceof ConnectionError) {
            console.error('[Chat] Connection failed:', error.message);
            this.ui.showError('Failed to connect to server');
            this._scheduleRetry();
        } else {
            console.error('[Chat] Unexpected error:', error);
            this.ui.showError('An unexpected error occurred');
        }
        throw error; // Re-throw for caller to handle
    }
}

// ❌ DON'T: Catch and ignore silently
async function badExample(content) {
    try {
        await this.api.send(content);
    } catch (error) {
        // Silent failure - bad practice!
    }
}
```

---

## 🧪 **Testing Requirements**

### **Unit Test Structure**

```javascript
/**
 * Test file: AuthService.test.js
 */
import { AuthService } from '../auth/AuthService.js';

describe('AuthService', () => {
    let authService;
    
    beforeEach(() => {
        authService = new AuthService();
    });
    
    describe('login()', () => {
        it('should successfully login with valid credentials', async () => {
            const result = await authService.login('user', 'pass');
            expect(result.token).toBeDefined();
            expect(result.user.username).toBe('user');
        });
        
        it('should throw AuthenticationError with invalid credentials', async () => {
            await expect(authService.login('user', 'wrong'))
                .rejects
                .toThrow(AuthenticationError);
        });
        
        it('should store token after successful login', async () => {
            await authService.login('user', 'pass');
            expect(authService.isAuthenticated()).toBe(true);
        });
    });
    
    describe('logout()', () => {
        it('should clear token and set isAuthenticated to false', async () => {
            await authService.login('user', 'pass');
            await authService.logout();
            expect(authService.isAuthenticated()).toBe(false);
        });
    });
});
```

---

## 🔒 **Security Best Practices**

### **Input Sanitization**

```javascript
/**
 * Sanitize user input to prevent XSS attacks
 */
class SecurityService {
    sanitizeHTML(input) {
        if (!input) return '';
        
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    }
    
    escapeHTML(input) {
        return input
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}
```

### **Token Storage**

```javascript
// ✅ DO: Use httpOnly cookies (server-side) when possible
// ✅ DO: Store tokens in memory for session duration
// ✅ DO: Clear tokens on logout
// ⚠️ CAUTION: localStorage/sessionStorage are vulnerable to XSS

class SecureTokenStorage {
    constructor() {
        this.token = null; // In-memory storage
    }
    
    setToken(token) {
        this.token = token;
        // Only store expiry in localStorage
        sessionStorage.setItem('token_expiry', Date.now() + 30 * 60 * 1000);
    }
    
    getToken() {
        const expiry = sessionStorage.getItem('token_expiry');
        if (!expiry || Date.now() > parseInt(expiry)) {
            this.clearToken();
            return null;
        }
        return this.token;
    }
    
    clearToken() {
        this.token = null;
        sessionStorage.removeItem('token_expiry');
    }
}
```

### **API Communication**

```javascript
// ✅ DO: Always use HTTPS in production
// ✅ DO: Validate responses
// ✅ DO: Handle errors gracefully

class APIService {
    async makeRequest(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const token = this.auth.getToken();
        
        const config = {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, config);
            
            // Always check response status
            if (!response.ok) {
                throw new APIError(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            
            // Validate response structure
            if (!this._isValidResponse(data)) {
                throw new ValidationError('Invalid response format');
            }
            
            return data;
        } catch (error) {
            console.error(`[API] Request failed: ${endpoint}`, error);
            throw error;
        }
    }
}
```

---

## 📚 **Additional Resources**

- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [JSDoc Official Documentation](https://jsdoc.app/)
- [Clean Code JavaScript](https://github.com/ryanmcdermott/clean-code-javascript)
- [OWASP JavaScript Security](https://owasp.org/www-project-web-security-testing-guide/)

---

**Last Updated:** 2025-10-15  
**Maintained By:** Socializer Development Team  
**Review Schedule:** Quarterly
