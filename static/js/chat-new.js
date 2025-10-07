/**
 * WebSocket-based Chat Application
 * 
 * This is the main entry point for the chat application.
 * It initializes all the necessary components and sets up the UI.
 */

// Import required modules
import { WebSocketService } from './modules/WebSocketService.js';
import { UserManager } from './modules/UserManager.js';
import { UIManager } from './modules/UIManager.js';
import { ChatController } from './modules/ChatController.js';
import { authService } from './auth/AuthService.js';

// ============================================
// Configuration
// ============================================

const CONFIG = {
    // WebSocket server URL (will be set based on current host)
    websocketUrl: (() => {
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const host = window.location.host;
        return `${protocol}${host}/ws/chat`;
    })(),
    
    // Chat room ID (can be made dynamic if needed)
    roomId: 'main',
    
    // Current user data (from template or create a guest user)
    currentUser: (() => {
        const user = window.currentUser || {
            id: `guest-${Math.random().toString(36).substr(2, 9)}`,
            username: 'Guest',
            email: ''
        };
        
        // Add room info to user object
        user.room = 'main';
        return user;
    })(),
    
    // Get authentication token
    token: (() => {
        const token = window.ACCESS_TOKEN || getTokenFromStorage();
        
        if (!token) {
            console.error('❌ No authentication token found');
            return null;
        }
        
        // Log token info (without exposing the full token)
        logTokenInfo(token);
        return token;
    })()
};

// ============================================
// Utility Functions
// ============================================

/**
 * Get token from browser storage
 * @returns {string|null} The authentication token or null if not found
 */
function getTokenFromStorage() {
    // Check cookies
    const cookieMatch = document.cookie.match(/access_token=([^;]+)/);
    if (cookieMatch && cookieMatch[1]) {
        return cookieMatch[1];
    }
    
    // Check localStorage
    return localStorage.getItem('access_token');
}

/**
 * Log token information (for debugging)
 * @param {string} token - The JWT token
 */
function logTokenInfo(token) {
    const tokenParts = token.split('.');
    if (tokenParts.length === 3) {
        try {
            const payload = JSON.parse(atob(tokenParts[1]));
            console.log('🔑 Token details:', {
                subject: payload.sub,
                expires: payload.exp ? new Date(payload.exp * 1000).toISOString() : 'No expiration',
                issued: payload.iat ? new Date(payload.iat * 1000).toISOString() : 'No issue time',
                tokenStart: token.substring(0, 5) + '...',
                tokenEnd: '...' + token.substring(token.length - 5)
            });
        } catch (e) {
            console.warn('⚠️ Could not parse token payload:', e);
        }
    } else {
        console.warn('⚠️ Token format appears to be invalid');
    }
}

// ============================================
// Application Initialization
// ============================================

/**
 * Initialize the chat application
 */
async function initialize() {
    console.log('🚀 Initializing chat application...');
    
    try {
        // Check if we have a valid token
        if (!CONFIG.token) {
            throw new Error('No authentication token available');
        }
        
        // Initialize managers
        const userManager = new UserManager(CONFIG.currentUser);
        
        // Get DOM elements
        const elements = {
            onlineUsersList: document.getElementById('online-users-list'),
            onlineCount: document.getElementById('online-count'),
            chatMessages: document.getElementById('chat-messages'),
            messageInput: document.getElementById('message-input'),
            sendButton: document.getElementById('send-button'),
            typingIndicator: document.getElementById('typing-indicator'),
            connectionStatus: document.getElementById('connection-status')
        };
        
        // Initialize UI Manager
        const uiManager = new UIManager(userManager, elements);
        
        // Initialize WebSocket Service
        if (!CONFIG.websocketUrl) {
            console.error('❌ Cannot initialize WebSocket: No valid URL');
            return;
        }
        
        const webSocketService = new WebSocketService(CONFIG.websocketUrl, {
            autoReconnect: true,
            maxReconnectAttempts: 5,
            reconnectInterval: 3000
        });
        
        // Initialize Chat Controller
        const chatController = new ChatController(
            webSocketService,
            userManager,
            uiManager,
            {
                websocketUrl: CONFIG.websocketUrl,
                roomId: CONFIG.roomId,
                currentUser: CONFIG.currentUser
            }
        );
        
        // Store references for debugging
        window.__chatApp = {
            controller: chatController,
            userManager,
            uiManager,
            webSocketService
        };
        
        // Set up logout button handler
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => {
                console.log('🚪 Logging out...');
                authService.logout();
            });
            console.log('✅ Logout button handler attached');
        } else {
            console.warn('⚠️ Logout button not found');
        }
        
        console.log('✅ Chat application initialized');
        
    } catch (error) {
        console.error('❌ Failed to initialize chat application:', error);
        
        // Show error to user
        const statusEl = document.getElementById('connection-status');
        if (statusEl) {
            statusEl.textContent = `Error: ${error.message}`;
            statusEl.className = 'connection-status error';
        }
        
        // Disable UI elements
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        
        if (messageInput) messageInput.disabled = true;
        if (sendButton) sendButton.disabled = true;
    }
}

// Start the application when the DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Check if we have a valid WebSocket URL before initializing
        if (CONFIG.websocketUrl) {
            initialize();
        } else {
            console.error('❌ Cannot initialize chat: Missing WebSocket URL or authentication');
            // Show error message to user
            const app = document.getElementById('app') || document.body;
            app.innerHTML = `
                <div style="padding: 20px; color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; margin: 20px;">
                    <h2>Authentication Required</h2>
                    <p>Please <a href="/login?next=${encodeURIComponent(window.location.pathname)}">log in</a> to use the chat.</p>
                </div>
            `;
        }
    });
} else {
    // DOMContentLoaded has already fired
    if (CONFIG.websocketUrl) {
        initialize();
    } else {
        console.error('❌ Cannot initialize chat: Missing WebSocket URL or authentication');
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    }
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initialize,
        getTokenFromStorage,
        logTokenInfo
    };
}
