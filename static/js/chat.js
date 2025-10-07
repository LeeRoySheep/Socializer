/**
 * WebSocket-based Chat Application
 * 
 * This module handles real-time chat functionality including:
 * - WebSocket connection management
 * - Message sending/receiving
 * - Online users list
 * - Typing indicators
 * - Connection status
 */

// Import AuthService for logout functionality
import { authService } from './auth/AuthService.js';

console.log('[CHAT] chat.js loaded');

// ============================================
// Configuration and Constants
// ============================================

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 3000; // 3 seconds
const TYPING_TIMEOUT = 2000; // 2 seconds
const PING_INTERVAL = 30000; // 30 seconds
const PONG_TIMEOUT = 10000;  // 10 seconds
const CHAT_ROOM = 'main'; // Default chat room

// ============================================
// State Management
// ============================================

let socket = null;
let reconnectAttempts = 0;
let pingInterval = null;
let reconnectTimeout = null;
let lastPongTime = null;
const typingUsers = new Set();
let typingTimer = null;
let currentRoom = CHAT_ROOM;

// Get user data from the template or create a guest user
const currentUser = window.currentUser || {
    id: `guest-${Math.random().toString(36).substr(2, 9)}`,
    username: 'Guest',
    email: ''
};

// Add room info to user object
currentUser.room = currentRoom;

// Get and validate the authentication token
const AUTH_TOKEN = (() => {
    const token = window.ACCESS_TOKEN || getTokenFromStorage();

    if (!token) {
        console.error('❌ No authentication token found');
        return null;
    }

    // Strip 'Bearer ' prefix if present (for WebSocket use)
    const cleanToken = token.replace(/^Bearer\s+/, '');
    console.log('🔑 Clean token for WebSocket:', cleanToken ? 'Token available' : 'No token');

    return cleanToken;
    
    // Log token info (without exposing the full token)
    const tokenParts = token.split('.');
    if (tokenParts.length === 3) {
        try {
            const payload = JSON.parse(atob(tokenParts[1]));
            console.log('🔑 Token details:', {
                subject: payload.sub,
                expires: payload.exp ? new Date(payload.exp * 1000).toISOString() : 'No expiration',
                issued: payload.iat ? new Date(payload.iat * 1000).toISOString() : 'No issue time',
                tokenStart: token.substring(0, 10) + '...',
                tokenEnd: '...' + token.substring(token.length - 10)
            });
        } catch (e) {
            console.warn('⚠️ Could not parse token payload:', e);
        }
    } else {
        console.warn('⚠️ Token format appears to be invalid');
    }
    
    return token;
})();

// ============================================
// DOM Elements
// ============================================

const elements = {
    messageInput: document.getElementById('message-input'),
    sendButton: document.getElementById('send-btn'),
    chatMessages: document.getElementById('messages'),
    onlineUsersList: document.getElementById('online-users-list'),
    typingIndicator: document.getElementById('typing-indicator'),
    connectionStatus: document.getElementById('connection-status'),
    onlineCount: document.getElementById('online-count'),
    toggleSidebarBtn: document.getElementById('toggle-sidebar'),
    chatSidebar: document.getElementById('left-sidebar'),
    messageForm: document.getElementById('message-form')
};

// ============================================
// Utility Functions
// ============================================

function getTokenFromStorage() {
    // Check cookies
    const cookies = document.cookie.split(';')
        .map(c => c.trim().split('='))
        .find(([name]) => name === 'access_token');
    
    if (cookies?.[1]) return cookies[1];
    
    // Check localStorage
    try {
        return localStorage.getItem('access_token');
    } catch (e) {
        console.warn('localStorage not available:', e);
        return null;
    }
}

/**
 * Get authentication token for WebSocket connection
 * Checks multiple sources in order of priority:
 * 1. AuthService (auth_token key)
 * 2. Cookies (access_token)
 * 3. localStorage (access_token)
 * @returns {string|null} Clean token without 'Bearer ' prefix
 */
function getAuthToken() {
    // Try AuthService first (stores as 'auth_token')
    try {
        const authTokenStr = localStorage.getItem('auth_token');
        if (authTokenStr) {
            const tokenData = JSON.parse(authTokenStr);
            if (tokenData && tokenData.access_token) {
                console.log('🔑 Token found in AuthService storage');
                return tokenData.access_token.replace(/^Bearer\s+/, '');
            }
        }
    } catch (e) {
        console.warn('Could not parse auth_token:', e);
    }
    
    // Fall back to cookies
    const cookieMatch = document.cookie.match(/access_token=([^;]+)/);
    if (cookieMatch && cookieMatch[1]) {
        console.log('🔑 Token found in cookies');
        return cookieMatch[1].replace(/^Bearer\s+/, '');
    }
    
    // Fall back to localStorage
    try {
        const token = localStorage.getItem('access_token');
        if (token) {
            console.log('🔑 Token found in localStorage');
            return token.replace(/^Bearer\s+/, '');
        }
    } catch (e) {
        console.warn('localStorage not available:', e);
    }
    
    console.error('❌ No authentication token found in any storage');
    return null;
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}


function updateCurrentUserDisplay() {
    // Display current username in sidebar
    const usernameDisplay = document.getElementById('username-display');
    if (usernameDisplay && window.currentUser) {
        usernameDisplay.textContent = window.currentUser.username;
    }
    
    // Also show current user in the online users list
    if (window.currentUser) {
        addUserToOnlineList(window.currentUser);
    }
}

function addUserToOnlineList(user) {
    if (!elements.onlineUsersList) return;
    
    // Check if user is already in the list
    const existingUser = elements.onlineUsersList.querySelector(`[data-user-id="${user.id}"]`);
    if (existingUser) return;
    
    const userDiv = document.createElement('div');
    userDiv.className = 'user-item';
    userDiv.setAttribute('data-user-id', user.id);
    userDiv.innerHTML = `
        <div class="user-avatar">${user.username.charAt(0).toUpperCase()}</div>
        <div class="user-info">
            <div class="user-name">${escapeHtml(user.username)} ${user.id === window.currentUser?.id ? '(You)' : ''}</div>
            <div class="user-status">Online</div>
        </div>
    `;
    
    elements.onlineUsersList.appendChild(userDiv);
}

function formatTime(date) {
    if (!date) return '';
    if (!(date instanceof Date)) date = new Date(date);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function getUserColor(userId) {
    if (!userId) return '#6c757d';
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
        hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return `hsl(${Math.abs(hash % 360)}, 70%, 60%)`;
}

function getWebSocketState(state) {
    const states = {
        0: 'CONNECTING',
        1: 'OPEN',
        2: 'CLOSING',
        3: 'CLOSED'
    };
    return states[state] || `UNKNOWN (${state})`;
}

// ============================================
// WebSocket Connection
// ============================================

function getWebSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const path = `/ws/chat`; // Match backend endpoint

    // Backend expects clean URL, token sent as first message
    const url = `${protocol}//${host}${path}`;
    console.log('🌐 WebSocket URL (no token in URL):', url);
    return url;
}

function setupPingPong() {
    if (pingInterval) {
        clearInterval(pingInterval);
    }
    
    lastPongTime = Date.now();
    
    pingInterval = setInterval(() => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            // First, send the ping
            try {
                const pingMsg = JSON.stringify({
                    type: 'ping',
                    timestamp: new Date().toISOString()
                });
                console.log('Sending ping:', pingMsg);
                socket.send(pingMsg);
            } catch (e) {
                console.error('Error sending ping:', e);
            }
            
            // Then check if previous pong was received
            // Allow extra time: PING_INTERVAL + PONG_TIMEOUT
            const timeSinceLastPong = Date.now() - lastPongTime;
            const maxAllowedTime = PING_INTERVAL + PONG_TIMEOUT;
            if (timeSinceLastPong > maxAllowedTime) {
                console.warn('No pong received in the last', timeSinceLastPong, 'ms (max:', maxAllowedTime, 'ms)');
                socket.close(4000, 'No pong received');
                return;
            }
        }
    }, PING_INTERVAL);
}

function removeUserFromOnlineList(userId) {
    if (!elements.onlineUsersList) return;
    
    const userElement = elements.onlineUsersList.querySelector(`[data-user-id="${userId}"]`);
    if (userElement) {
        userElement.remove();
        
        // Update count
        const currentCount = elements.onlineUsersList.children.length;
        if (elements.onlineCount) {
            elements.onlineCount.textContent = `${currentCount} online`;
        }
    }
}

function handleIncomingMessage(event) {
    let message;
    try {
        message = JSON.parse(event.data);
        console.log('📨 Received message:', message);
    } catch (e) {
        console.error('Error parsing message:', e, event.data);
        return;
    }
    
    if (!message || !message.type) {
        console.warn('Received message with no type:', message);
        return;
    }
    
    // Log all incoming messages for debugging
    console.log(`[${new Date().toISOString()}] Received message type:`, message.type);
    
    switch (message.type) {
        case 'pong':
            lastPongTime = Date.now();
            console.log('Received pong');
            break;
            
        case 'online_users':
            console.log('Updating online users:', message.users);
            updateOnlineUsersList(message.users || []);
            break;
            
        case 'chat_message':
            displayMessage({
                sender: {
                    id: message.user_id,
                    username: message.username
                },
                content: message.content,
                timestamp: message.timestamp,
                messageType: 'chat_message'
            });
            break;
            
        case 'user_joined':
            displayMessage({
                sender: 'System',
                content: `${message.username} has joined the chat`,
                timestamp: message.timestamp,
                messageType: 'system'
            });
            // Request updated online users list
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'get_online_users' }));
            }
            break;
            
        case 'user_left':
            displayMessage({
                sender: 'System',
                content: `${message.username} has left the chat`,
                timestamp: message.timestamp,
                messageType: 'system'
            });
            // Request updated online users list
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'get_online_users' }));
            }
            break;
            
        case 'user_typing':
            updateTypingIndicator({
                username: message.username,
                isTyping: message.is_typing
            });
            break;
            
        case 'connection_established':
            console.log('✅ Authentication successful!');
            displayMessage({
                sender: 'System',
                content: message.message || 'Successfully connected to chat',
                timestamp: message.timestamp,
                messageType: 'system'
            });
            // Request online users list after successful authentication
            if (socket && socket.readyState === WebSocket.OPEN) {
                console.log('📤 Requesting online users list...');
                socket.send(JSON.stringify({ 
                    type: 'get_online_users',
                    timestamp: new Date().toISOString()
                }));
            }
            break;
            
        case 'error':
            console.error('❌ Server error:', message.message);
            displayMessage({
                sender: 'System',
                content: `Error: ${message.message}`,
                timestamp: new Date().toISOString(),
                messageType: 'error'
            });
            break;
            
        default:
            console.warn('Unknown message type:', message.type, message);
    }
}

/**
 * Properly close WebSocket connection and prevent reconnection
 */
function closeWebSocket() {
    console.log('Closing WebSocket connection...');
    
    // Clear reconnection timeout
    if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
        reconnectTimeout = null;
    }
    
    // Clear ping interval
    if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
    }
    
    // Set reconnect attempts to max to prevent reconnection
    reconnectAttempts = MAX_RECONNECT_ATTEMPTS;
    
    // Close the socket if it exists
    if (socket) {
        socket.close(1000, 'User logout');
        socket = null;
    }
    
    console.log('WebSocket closed and cleanup complete');
}

// Export closeWebSocket for use in logout
window.closeWebSocket = closeWebSocket;

function initWebSocket() {
    console.log('Initializing WebSocket connection...');
    
    if (!AUTH_TOKEN) {
        const error = 'No authentication token available';
        console.error(error);
        updateConnectionStatus(false, 'Authentication required');
        return Promise.reject(new Error(error));
    }

    closeExistingConnection();
    updateConnectionStatus(false, 'Connecting to chat...');

    return new Promise((resolve, reject) => {
        try {
            const wsUrl = getWebSocketUrl();
            console.log('🔌 Connecting to WebSocket...');
            
            // Create WebSocket (backend expects token as first message)
            console.log('Using WebSocket (token sent as first message)');
            socket = new WebSocket(wsUrl);
            socket.binaryType = 'arraybuffer';
            
            // WebSocket event handlers
            socket.onopen = (event) => {
                console.log('✅ WebSocket connection established', event);
                console.log('Protocols:', socket.protocol);
                reconnectAttempts = 0;
                updateConnectionStatus(true, 'Connected');
                
                // Start ping-pong
                setupPingPong();
                
                // Send authentication as first message
                try {
                    // Get token from storage
                    const token = getAuthToken();
                    
                    if (!token) {
                        console.error('❌ No authentication token found!');
                        socket.close(4003, 'No authentication token');
                        reject(new Error('No authentication token'));
                        return;
                    }
                    
                    // Send auth message
                    const authMessage = {
                        type: 'auth',
                        token: token,
                        username: currentUser.username  // Include username for convenience
                    };
                    console.log('📤 Sending authentication message...');
                    console.log('   Token length:', token.length);
                    console.log('   Token preview:', token.substring(0, 20) + '...');
                    socket.send(JSON.stringify(authMessage));
                    
                    // Note: Don't send other messages yet - wait for auth confirmation
                    // The server will respond with connection_established on success
                    
                    resolve();
                } catch (e) {
                    console.error('Error during authentication:', e);
                    reject(e);
                }
            };
            
            socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    console.log('📨 Received message:', message);
                    
                    // Update last pong time when we receive a pong
                    if (message.type === 'pong') {
                        lastPongTime = Date.now();
                        console.log('Received pong at:', new Date().toISOString());
                        return;
                    }
                    
                    // Handle other message types
                    handleIncomingMessage({ data: event.data });
                } catch (e) {
                    console.error('Error processing message:', e, event.data);
                }
            };
            
            socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                updateConnectionStatus(false, 'Connection error');
            };
            
            socket.onclose = (event) => {
                console.log('❌ WebSocket closed:', {
                    code: event.code,
                    reason: event.reason,
                    wasClean: event.wasClean
                });
                
                updateConnectionStatus(false, 'Disconnected');
                clearInterval(pingInterval);
                
                // Attempt to reconnect if not a normal closure
                if (event.code !== 1000 && reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
                    const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                    console.log(`Attempting to reconnect in ${delay}ms... (attempt ${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);
                    
                    reconnectTimeout = setTimeout(() => {
                        reconnectAttempts++;
                        console.log(`Reconnection attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
                        initWebSocket().catch(console.error);
                    }, delay);
                } else if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                    console.error('❌ Max reconnection attempts reached. Please refresh the page.');
                    updateConnectionStatus(false, 'Connection failed - Please refresh');
                }
            };
        } catch (error) {
            console.error('Error initializing WebSocket:', error);
            updateConnectionStatus(false, 'Connection failed');
            reject(error);
        }
    });
}

function closeExistingConnection() {
    if (socket) {
        try {
            socket.onclose = null;
            socket.close();
        } catch (e) {
            console.error('Error closing WebSocket:', e);
        } finally {
            socket = null;
        }
    }
    
    if (pingInterval) {
        clearInterval(pingInterval);
        pingInterval = null;
    }
}

// ============================================
// Message Handling
// ============================================

function sendMessage(content) {
    console.log('📤 sendMessage called with:', content);
    
    if (!socket || socket.readyState !== WebSocket.OPEN) {
        console.error('Cannot send message: WebSocket is not connected');
        updateConnectionStatus(false, 'Not connected');
        return false;
    }

    try {
        const message = {
            type: 'chat_message',
            content: escapeHtml(content),
            timestamp: new Date().toISOString()
        };
        
        console.log('📤 Sending message:', message);
        socket.send(JSON.stringify(message));
        console.log('✅ Message sent successfully');
        return true;
    } catch (error) {
        console.error('Error sending message:', error);
        return false;
    }
}

function sendTypingIndicator(isTyping) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    
    try {
        const message = {
            type: 'typing',
            isTyping: isTyping,
            timestamp: new Date().toISOString()
        };
        
        socket.send(JSON.stringify(message));
    } catch (error) {
        console.error('Error sending typing indicator:', error);
    }
}

// ============================================
// UI Updates
// ============================================

function updateConnectionStatus(connected, message = '') {
    if (!elements.connectionStatus) return;
    
    elements.connectionStatus.textContent = message;
    elements.connectionStatus.className = connected ? 'connected' : 'disconnected';
}

function displayMessage({ sender, content, messageType = 'chat_message', timestamp }) {
    if (!elements.chatMessages) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${messageType}`;
    
    const timeString = formatTime(timestamp);
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="sender" style="color: ${getUserColor(sender.id || sender)}">
                ${escapeHtml(sender.username || sender)}
            </span>
            <span class="time">${timeString}</span>
        </div>
        <div class="message-content">${content}</div>
    `;
    
    elements.chatMessages.appendChild(messageElement);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

function updateOnlineUsersList(users) {
    console.log('Updating online users list with:', users);
    
    if (!elements.onlineUsersList || !elements.onlineCount) {
        console.warn('Online users list or count element not found');
        return;
    }
    
    try {
        // Ensure users is an array
        if (!Array.isArray(users)) {
            console.warn('Expected users to be an array, got:', typeof users);
            users = [];
        }
        
        // Process users array
        const uniqueUsers = [];
        const userMap = new Map();
        
        users.forEach(user => {
            try {
                // Handle different possible user object structures
                const userId = user.id || user.user_id || '';
                const username = user.username || 'Unknown';
                const status = user.status || 'online';
                
                if (userId && !userMap.has(userId)) {
                    userMap.set(userId, true);
                    uniqueUsers.push({
                        id: userId,
                        username: username,
                        status: status,
                        lastSeen: user.last_seen || user.lastSeen || null
                    });
                }
            } catch (e) {
                console.error('Error processing user:', user, e);
            }
        });
        
        // Update count
        const count = uniqueUsers.length;
        if (elements.onlineCount) {
            elements.onlineCount.textContent = `${count} online`;
        }
        
        // Update list
        if (count === 0) {
            elements.onlineUsersList.innerHTML = '<li class="no-users">No users online</li>';
            return;
        }
        
        // Sort users by username
        const sortedUsers = [...uniqueUsers].sort((a, b) => 
            a.username.localeCompare(b.username)
        );
        
        // Generate HTML for each user
        elements.onlineUsersList.innerHTML = sortedUsers
            .map(user => {
                const isCurrentUser = user.id === currentUser.id;
                const displayName = isCurrentUser ? `${user.username} (You)` : user.username;
                const statusClass = user.status === 'online' ? 'online' : 'offline';
                const statusTitle = user.status === 'online' ? 'Online' : 'Offline';
                
                return `
                    <li class="online-user ${isCurrentUser ? 'current-user' : ''}" data-user-id="${user.id}">
                        <span class="user-status ${statusClass}" title="${statusTitle}"></span>
                        <span class="username" style="color: ${getUserColor(user.id)}">
                            ${escapeHtml(displayName)}
                        </span>
                        ${user.status !== 'online' ? `
                            <span class="last-seen" title="Last seen: ${user.lastSeen || 'Unknown'}">
                                (offline)
                            </span>
                        ` : ''}
                    </li>
                `;
            })
            .join('');
        
        console.log('Updated online users list with', count, 'users');
        
    } catch (error) {
        console.error('Error updating online users list:', error);
        elements.onlineUsersList.innerHTML = '<li class="error">Error loading users</li>';
    }
}

function updateTypingIndicator(typingData) {
    if (!elements.typingIndicator) return;
    
    if (typingData.isTyping) {
        typingUsers.add(typingData.username);
    } else {
        typingUsers.delete(typingData.username);
    }
    
    // Clear any existing timeout
    if (typingTimer) {
        clearTimeout(typingTimer);
    }
    
    if (typingUsers.size > 0) {
        const names = Array.from(typingUsers);
        let message = names[0] + (names.length > 1 ? ' and others are' : ' is') + ' typing...';
        elements.typingIndicator.textContent = message;
        elements.typingIndicator.style.display = 'block';
        
        // Auto-hide after 3 seconds of no typing
        typingTimer = setTimeout(() => {
            elements.typingIndicator.style.display = 'none';
            typingUsers.clear();
        }, 3000);
    } else {
        elements.typingIndicator.style.display = 'none';
    }
}

// ============================================
// Event Handlers
// ============================================

function handleMessageSubmit(event) {
    event.preventDefault();
    console.log('📝 handleMessageSubmit called');
    
    const messageInput = elements.messageInput;
    const content = messageInput.value.trim();
    
    console.log('Message input value:', content);
    console.log('Socket state:', socket ? socket.readyState : 'null');
    
    if (content && socket && socket.readyState === WebSocket.OPEN) {
        if (sendMessage(content)) {
            messageInput.value = '';
            sendTypingIndicator(false);
        }
    } else {
        if (!content) console.warn('No content to send');
        if (!socket) console.error('Socket is null');
        if (socket && socket.readyState !== WebSocket.OPEN) console.error('Socket not open, state:', socket.readyState);
    }
}

function handleTyping() {
    if (!typingTimer) {
        sendTypingIndicator(true);
    }
    
    // Reset the timer
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => {
        sendTypingIndicator(false);
        typingTimer = null;
    }, TYPING_TIMEOUT);
}

// ============================================
// Initialization
// ============================================

function setupEventListeners() {
    // Message form
    if (elements.messageForm) {
        elements.messageForm.addEventListener('submit', handleMessageSubmit);
    }
    
    // Typing indicator
    if (elements.messageInput) {
        elements.messageInput.addEventListener('input', handleTyping);
        
        // Enter key to send message
        elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (elements.messageForm) {
                    elements.messageForm.dispatchEvent(new Event('submit'));
                }
            }
        });
    }
    
    // Toggle sidebar
    if (elements.toggleSidebarBtn && elements.chatSidebar) {
        elements.toggleSidebarBtn.addEventListener('click', () => {
            elements.chatSidebar.classList.toggle('collapsed');
        });
    }
    

    // Private chat button
    const privateChatBtn = document.getElementById('private-chat-btn');
    if (privateChatBtn) {
        privateChatBtn.addEventListener('click', () => {
            console.log('[CHAT] Private chat button clicked');
            // TODO: Implement private chat functionality
            alert('Private chat feature coming soon!');
        });
        console.log('[CHAT] Private chat button handler attached');
    }

    // AI response button
    const aiBtn = document.getElementById('ai-btn');
    if (aiBtn) {
        aiBtn.addEventListener('click', () => {
            console.log('[CHAT] AI response button clicked');
            // TODO: Implement AI response functionality
            alert('AI response feature coming soon!');
        });
        console.log('[CHAT] AI response button handler attached');
    }
    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    console.log('[CHAT] Looking for logout button, found:', logoutBtn);
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault(); // Prevent any default behavior
            console.log('[CHAT] Logout button clicked!');
            console.log('[CHAT] AuthService:', authService);
            try {
                // Close WebSocket connection BEFORE logging out
                console.log('[CHAT] Closing WebSocket before logout...');
                closeWebSocket();
                
                // Small delay to ensure WebSocket closes properly
                setTimeout(() => {
                    authService.logout();
                    console.log('[CHAT] Logout called successfully');
                }, 100);
            } catch (error) {
                console.error('[CHAT] Error during logout:', error);
                // Even if error, try to logout
                authService.logout();
            }
        });
        console.log('[CHAT] Logout button handler attached');
    } else {
        console.warn('[CHAT] Logout button not found in DOM');
    }
}

async function initialize() {
    console.log('Initializing chat application...');
    
    try {
        // Display current user info in sidebar
        updateCurrentUserDisplay();
        
        setupEventListeners();
        await initWebSocket();
        console.log('Chat application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize chat application:', error);
        updateConnectionStatus(false, 'Failed to connect');
    }
}

// Close WebSocket when page unloads
window.addEventListener('beforeunload', () => {
    console.log('[CHAT] Page unloading, closing WebSocket...');
    closeWebSocket();
});

// Start the application when the DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    // DOM already loaded, initialize immediately
    initialize().catch(console.error);
}
