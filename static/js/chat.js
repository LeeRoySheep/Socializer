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

// AI Assistant State
let isAIActive = false;
let isListening = false;
let aiTypingIndicator = null;
let passiveListeningTimer = null;
let lastSuggestedHelp = 0;

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
// AI Assistant Functions
// ============================================

// Track if auto-assistance mode is enabled
let autoAssistanceEnabled = true; // Default: ON

// Store recent conversation context for AI monitoring
let conversationContext = [];
const MAX_CONTEXT_MESSAGES = 10;

// Throttle AI monitoring to avoid too many requests
let lastMonitoringTime = 0;
const MONITORING_THROTTLE_MS = 3000; // Only monitor every 3 seconds max

function addToConversationContext(username, content) {
    conversationContext.push({
        username: username,
        content: content,
        timestamp: Date.now()
    });
    
    // Keep only last N messages
    if (conversationContext.length > MAX_CONTEXT_MESSAGES) {
        conversationContext.shift();
    }
}

function monitorConversationForAssistance(content, username) {
    if (!isAIActive || !content || !autoAssistanceEnabled) return;
    
    console.log('[AI] 🔍 AI monitoring conversation from:', username);
    
    // Add to context (always track context)
    addToConversationContext(username, content);
    
    // Throttle monitoring requests
    const now = Date.now();
    const timeSinceLastMonitoring = now - lastMonitoringTime;
    
    if (timeSinceLastMonitoring < MONITORING_THROTTLE_MS) {
        console.log(`[AI] Monitoring throttled (wait ${Math.ceil((MONITORING_THROTTLE_MS - timeSinceLastMonitoring) / 1000)}s)`);
        return;
    }
    
    lastMonitoringTime = now;
    
    // Send conversation context to AI agent for intelligent monitoring
    // The AI agent will decide if intervention is needed
    const contextSummary = conversationContext.slice(-5).map(msg => 
        `${msg.username}: ${msg.content}`
    ).join('\n');
    
    console.log('[AI] Sending context to AI for monitoring:', {
        messageCount: conversationContext.length,
        latestMessage: `${username}: ${content}`
    });
    
    // Send to AI agent with special monitoring prompt
    // The AI will respond ONLY if it detects a need for help
    sendConversationForMonitoring(contextSummary, username, content);
}

async function sendConversationForMonitoring(contextSummary, username, latestContent) {
    try {
        // Create monitoring request
        const monitoringPrompt = `CONVERSATION MONITORING REQUEST

Latest message from ${username}: "${latestContent}"

Recent conversation context:
${contextSummary}

INSTRUCTIONS:
- You are monitoring this conversation in real-time
- Analyze if intervention is needed for:
  * Foreign language barriers (any language)
  * Confusion or misunderstandings (expressed in any language)
  * Communication breakdown
  * Cultural misunderstandings
  
- If intervention IS needed: Provide translation, clarification, or explanation directly
- If intervention is NOT needed: Respond with exactly "NO_INTERVENTION_NEEDED"
- Be proactive - help immediately when you detect issues
- Work with ALL languages, not just English

Should you intervene?`;

        const response = await fetch('/api/ai-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            },
            body: JSON.stringify({
                message: monitoringPrompt,
                thread_id: `chat-monitor-${currentUser.id}`
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('[AI] 📥 AI monitoring response received:', {
                hasResponse: !!data.response,
                responsePreview: data.response ? data.response.substring(0, 100) : 'null',
                toolsUsed: data.tools_used
            });
            
            // Check if AI decided to intervene
            if (data.response && !data.response.includes('NO_INTERVENTION_NEEDED')) {
                console.log('[AI] ✅ AI decided to intervene:', data.response.substring(0, 100));
                
                console.log('[AI] 🎬 Calling displayAIMessage...');
                // Display AI's intervention
                displayAIMessage(data.response, data.tools_used);
                console.log('[AI] 🎬 displayAIMessage call completed');
                
                console.log('[AI] 🎬 Calling displaySystemMessage...');
                displaySystemMessage(
                    '🤖 AI detected a communication issue and is helping... (Type "/ai stop" to disable)',
                    'info-message'
                );
                console.log('[AI] 🎬 displaySystemMessage call completed');
            } else {
                console.log('[AI] ℹ️ AI monitoring - no intervention needed');
            }
        } else {
            console.error('[AI] ❌ AI monitoring response not OK:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('[AI] Monitoring error (silent):', error);
        // Fail silently - don't disrupt user experience
    }
}

function startPassiveListening() {
    console.log('[AI] Starting passive listening...');
    const messageInput = document.getElementById('message-input');
    
    if (!messageInput) return;
    
    // Clear any existing listener
    stopPassiveListening();
    
    // Add input listener for passive help
    messageInput.addEventListener('input', handlePassiveListening);
    console.log('[AI] Passive listening active');
}

function stopPassiveListening() {
    console.log('[AI] Stopping passive listening...');
    const messageInput = document.getElementById('message-input');
    
    if (messageInput) {
        messageInput.removeEventListener('input', handlePassiveListening);
    }
    
    if (passiveListeningTimer) {
        clearTimeout(passiveListeningTimer);
        passiveListeningTimer = null;
    }
}

function handlePassiveListening(event) {
    if (!isAIActive || !isListening) {
        console.log('[AI] Passive listening inactive:', { isAIActive, isListening });
        return;
    }
    
    const text = event.target.value.trim();
    console.log('[AI] Input changed:', text);
    
    // Clear existing timer
    if (passiveListeningTimer) {
        clearTimeout(passiveListeningTimer);
    }
    
    // Wait for user to stop typing for 2 seconds
    passiveListeningTimer = setTimeout(() => {
        if (!text) {
            console.log('[AI] No text, skipping suggestion');
            return;
        }
        
        console.log('[AI] Analyzing text for suggestions:', text);
        
        // Check if message looks like a question or request for help
        const isQuestion = text.endsWith('?');
        const hasHelpKeywords = /\b(help|how|what|where|when|why|who|can you|could you|please|advice|tip|suggest)\b/i.test(text);
        
        // Check for translation requests (more lenient)
        const hasTranslateKeywords = /\b(translate|translation|traduce|traduire|übersetzen|mean|how do you say|what does|como se dice)\b/i.test(text);
        
        // Check for non-ASCII characters (possible foreign language) - lowered threshold to 5 chars
        const hasNonAscii = /[^\x00-\x7F]/.test(text);
        const likelyForeignLanguage = hasNonAscii && text.length > 5;
        
        console.log('[AI] Detection results:', {
            isQuestion,
            hasHelpKeywords,
            hasTranslateKeywords,
            hasNonAscii,
            likelyForeignLanguage,
            textLength: text.length
        });
        
        // Don't suggest too frequently (max once per 30 seconds)
        const now = Date.now();
        const timeSinceLastSuggestion = now - lastSuggestedHelp;
        if (timeSinceLastSuggestion < 30000) {
            console.log('[AI] Rate limited, wait:', Math.ceil((30000 - timeSinceLastSuggestion) / 1000), 'seconds');
            return;
        }
        
        if (isQuestion || hasHelpKeywords || hasTranslateKeywords || likelyForeignLanguage) {
            console.log('[AI] Creating suggestion!');
            lastSuggestedHelp = now;
            
            // Store the text that triggered the suggestion
            const capturedText = text;
            
            // Create suggestion element
            const messagesContainer = document.getElementById('messages');
            if (!messagesContainer) return;
            
            const suggestionDiv = document.createElement('div');
            suggestionDiv.className = 'message info-message ai-suggestion';
            suggestionDiv.style.cursor = 'pointer';
            suggestionDiv.style.transition = 'all 0.3s ease';
            suggestionDiv.style.userSelect = 'none';
            suggestionDiv.setAttribute('role', 'button');
            suggestionDiv.setAttribute('tabindex', '0');
            console.log('[AI] Suggestion element created');
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            
            // Determine suggestion message based on what triggered it
            let suggestionText = 'Would you like me to help with that?';
            let icon = '💡';
            
            if (hasTranslateKeywords) {
                suggestionText = 'Need help with translation?';
                icon = '🌐';
            } else if (likelyForeignLanguage) {
                suggestionText = 'Would you like me to translate or help with this?';
                icon = '🌐';
            } else if (isQuestion) {
                suggestionText = 'I can help answer that question!';
                icon = '💡';
            }
            
            contentDiv.innerHTML = `
                ${icon} <strong>AI Suggestion:</strong> ${suggestionText}<br>
                <small style="opacity: 0.8; display: block; margin-top: 4px;">"${capturedText.substring(0, 50)}${capturedText.length > 50 ? '...' : ''}"</small>
                <small style="opacity: 0.7; display: block; margin-top: 4px;">👆 Click anywhere on this box to ask AI</small>
            `;
            
            // Ensure content doesn't block clicks
            contentDiv.style.pointerEvents = 'none';
            
            suggestionDiv.appendChild(contentDiv);
            
            // Test: Add multiple event listeners to debug
            console.log('[AI] Attaching click handlers...');
            
            // Handler 1: Simple test (should ALWAYS fire)
            suggestionDiv.onclick = function() {
                console.log('[AI] 🎯 ONCLICK FIRED! (This proves element is clickable)');
                alert('Suggestion clicked! Check console for details.');
            };
            
            // Handler 2: addEventListener (our main handler)
            suggestionDiv.addEventListener('click', function(e) {
                console.log('[AI] 🎯 CLICK EVENT LISTENER FIRED!');
                console.log('[AI] Event details:', {
                    type: e.type,
                    target: e.target,
                    currentTarget: e.currentTarget,
                    bubbles: e.bubbles,
                    capturedText: capturedText
                });
                
                e.preventDefault();
                e.stopPropagation();
                
                console.log('[AI] ✅ Processing click with captured text:', capturedText);
                
                try {
                    // Send to AI
                    console.log('[AI] Calling handleAICommand...');
                    handleAICommand(`/ai ${capturedText}`);
                    console.log('[AI] ✅ Command sent successfully');
                    
                    // Clear input
                    const input = document.getElementById('message-input');
                    if (input) {
                        input.value = '';
                        console.log('[AI] ✅ Input cleared');
                    }
                    
                    // Remove suggestion
                    suggestionDiv.remove();
                    console.log('[AI] ✅ Suggestion removed');
                } catch (error) {
                    console.error('[AI] ❌ Error handling click:', error);
                    alert('Error: ' + error.message);
                }
            }, false);
            
            // Handler 3: Mousedown (backup)
            suggestionDiv.addEventListener('mousedown', function() {
                console.log('[AI] 🖱️ MOUSEDOWN detected');
            });
            
            // Handler 4: Mouseup (backup)
            suggestionDiv.addEventListener('mouseup', function() {
                console.log('[AI] 🖱️ MOUSEUP detected');
            });
            
            console.log('[AI] ✅ All click handlers attached');
            
            // Add hover effect
            suggestionDiv.addEventListener('mouseenter', () => {
                suggestionDiv.style.transform = 'scale(1.02)';
                suggestionDiv.style.boxShadow = '0 4px 12px rgba(33, 150, 243, 0.3)';
            });
            
            suggestionDiv.addEventListener('mouseleave', () => {
                suggestionDiv.style.transform = 'scale(1)';
                suggestionDiv.style.boxShadow = 'none';
            });
            
            messagesContainer.appendChild(suggestionDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
            console.log('[AI] ✅ Suggestion added to DOM and visible');
            
            // Add keyboard support (Enter/Space to activate)
            suggestionDiv.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    suggestionDiv.click();
                }
            });
            
            // Auto-remove after 10 seconds
            setTimeout(() => {
                if (suggestionDiv.parentNode) {
                    suggestionDiv.style.opacity = '0';
                    setTimeout(() => suggestionDiv.remove(), 300);
                }
            }, 10000);
        } else {
            console.log('[AI] ❌ No trigger matched - no suggestion created');
        }
    }, 2000); // Wait 2 seconds after user stops typing
}

function toggleAIAssistant() {
    isAIActive = !isAIActive;
    const toggleBtn = document.getElementById('ai-toggle');
    const toggleText = toggleBtn.querySelector('.ai-toggle-text');
    const listeningIndicator = document.getElementById('ai-listening-indicator');
    
    if (isAIActive) {
        toggleBtn.classList.add('active');
        toggleText.textContent = 'AI On';
        listeningIndicator.classList.add('active');
        isListening = true;
        displaySystemMessage('🤖 AI Assistant activated! I\'m passively listening. Type normally or use /ai for direct questions.', 'info-message');
        localStorage.setItem('aiAssistantEnabled', 'true');
        
        // Start passive listening
        startPassiveListening();
    } else {
        toggleBtn.classList.remove('active');
        toggleText.textContent = 'AI Off';
        listeningIndicator.classList.remove('active');
        isListening = false;
        displaySystemMessage('AI Assistant deactivated.', 'info-message');
        localStorage.setItem('aiAssistantEnabled', 'false');
        
        // Stop passive listening
        stopPassiveListening();
    }
}

function showAITypingIndicator() {
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;
    
    // Remove any existing typing indicator
    hideAITypingIndicator();
    
    const typingDiv = document.createElement('div');
    typingDiv.id = 'ai-typing-indicator';
    typingDiv.className = 'message ai-typing';
    typingDiv.innerHTML = `
        <span></span>
        <span></span>
        <span></span>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    aiTypingIndicator = typingDiv;
}

function hideAITypingIndicator() {
    if (aiTypingIndicator) {
        aiTypingIndicator.remove();
        aiTypingIndicator = null;
    }
    const existing = document.getElementById('ai-typing-indicator');
    if (existing) {
        existing.remove();
    }
}

async function handleAICommand(message) {
    const aiPrompt = message.replace(/^\/ai\s*/i, '').trim();
    
    // Check for "stop" command (stop AI monitoring/assistance)
    if (/^stop/i.test(aiPrompt)) {
        autoAssistanceEnabled = false;
        console.log('[AI] Auto-assistance mode DISABLED by user');
        displaySystemMessage(
            '✋ AI monitoring stopped. I will no longer automatically help with translations or clarifications. ' +
            'Type "/ai start" to re-enable.',
            'info-message'
        );
        return;
    }
    
    // Check for "start" command (start AI monitoring/assistance)
    if (/^start/i.test(aiPrompt)) {
        autoAssistanceEnabled = true;
        console.log('[AI] Auto-assistance mode ENABLED by user');
        displaySystemMessage(
            '✅ AI monitoring enabled. I will automatically detect and help with language barriers and misunderstandings.',
            'info-message'
        );
        return;
    }
    
    if (!aiPrompt) {
        displaySystemMessage('Please provide a question after /ai. Example: /ai What\'s the weather?', 'info-message');
        return;
    }
    
    // Show typing indicator
    showAITypingIndicator();
    
    try {
        const response = await fetch('/api/ai-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            },
            body: JSON.stringify({
                message: aiPrompt,
                thread_id: `chat-${currentUser.id}`
            })
        });
        
        hideAITypingIndicator();
        
        if (response.ok) {
            const data = await response.json();
            displayAIMessage(data.response, data.tools_used);
        } else {
            const errorData = await response.json();
            displaySystemMessage(`❌ AI Error: ${errorData.detail || 'Unknown error'}`, 'error-message');
        }
    } catch (error) {
        hideAITypingIndicator();
        console.error('AI Error:', error);
        displaySystemMessage('❌ Failed to connect to AI assistant. Please try again.', 'error-message');
    }
}

function displaySystemMessage(text, className = 'system-message') {
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${className}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = escapeHtml(text);
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function displayAIMessage(text, tools = null) {
    console.log('[AI] 📨 displayAIMessage called with text:', text.substring(0, 100));
    
    const messagesContainer = document.getElementById('messages');
    if (!messagesContainer) {
        console.error('[AI] ❌ Messages container not found!');
        return;
    }
    
    console.log('[AI] ✅ Messages container found');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    try {
        contentDiv.innerHTML = `<strong>🤖 AI Assistant:</strong><br>${escapeHtml(text)}`;
        console.log('[AI] ✅ Content HTML set');
    } catch (error) {
        console.error('[AI] ❌ Error setting innerHTML:', error);
        contentDiv.innerHTML = `<strong>🤖 AI Assistant:</strong><br>${text}`;
    }
    
    if (tools && tools.length > 0) {
        const toolsInfo = document.createElement('div');
        toolsInfo.style.fontSize = '0.75rem';
        toolsInfo.style.marginTop = '0.5rem';
        toolsInfo.style.opacity = '0.8';
        toolsInfo.innerHTML = `<i class="bi bi-tools"></i> Tools: ${tools.join(', ')}`;
        contentDiv.appendChild(toolsInfo);
        console.log('[AI] ✅ Tools info added');
    }
    
    messageDiv.appendChild(contentDiv);
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    console.log('[AI] ✅ AI message displayed successfully');
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
            
            // AI Intelligent Monitoring - Let AI agent decide when to help
            console.log('[AI] Passing message to AI for intelligent monitoring:', {
                isAIActive,
                username: message.username,
                content: message.content
            });
            
            if (isAIActive && autoAssistanceEnabled) {
                // Send ALL messages to AI for monitoring
                // AI will decide if translation, clarification, or help is needed
                // Works with ALL languages, not just English patterns
                monitorConversationForAssistance(message.content, message.username);
            } else {
                console.log('[AI] Monitoring disabled:', {
                    aiActive: isAIActive,
                    autoAssist: autoAssistanceEnabled
                });
            }
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
    
    // Check for AI command
    if (content.toLowerCase().startsWith('/ai')) {
        console.log('🤖 AI command detected');
        handleAICommand(content);
        messageInput.value = '';
        return;
    }
    
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

    // AI Toggle button
    const aiToggle = document.getElementById('ai-toggle');
    if (aiToggle) {
        aiToggle.addEventListener('click', () => {
            console.log('[CHAT] AI toggle clicked');
            toggleAIAssistant();
        });
        console.log('[CHAT] AI toggle handler attached');
    }

    // AI response button
    const aiBtn = document.getElementById('ai-btn');
    if (aiBtn) {
        aiBtn.addEventListener('click', () => {
            console.log('[CHAT] AI button clicked');
            const input = elements.messageInput;
            if (input) {
                const currentText = input.value.trim();
                if (currentText) {
                    // User has typed something - send it to AI
                    console.log('[CHAT] Sending existing text to AI:', currentText);
                    handleAICommand(`/ai ${currentText}`);
                    input.value = '';
                } else {
                    // No text - prompt user to type
                    input.value = '/ai ';
                    input.focus();
                }
            }
        });
        console.log('[CHAT] AI button handler attached');
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
        
        // Restore AI assistant state from localStorage
        const aiEnabled = localStorage.getItem('aiAssistantEnabled') === 'true';
        if (aiEnabled) {
            console.log('🤖 Restoring AI assistant state');
            const toggleBtn = document.getElementById('ai-toggle');
            const toggleText = toggleBtn?.querySelector('.ai-toggle-text');
            const listeningIndicator = document.getElementById('ai-listening-indicator');
            
            if (toggleBtn && toggleText) {
                isAIActive = true;
                isListening = true;
                toggleBtn.classList.add('active');
                toggleText.textContent = 'AI On';
                
                if (listeningIndicator) {
                    listeningIndicator.classList.add('active');
                }
                
                // Start passive listening
                startPassiveListening();
                console.log('🤖 Passive listening enabled');
            }
        }
        
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
