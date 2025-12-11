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

// Import PrivateRoomsManager for private chat rooms
import { privateRoomsManager } from './chat/PrivateRooms.js';

// Import LocalLLM for direct browser-to-LM Studio connection
import { localLLM } from './modules/LocalLLM.js';

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

        // Get selected LLM model from dropdown
        const selectedModel = window.getCurrentLLMModel ? window.getCurrentLLMModel() : 'gpt-4o-mini';
        
        const response = await fetch('/api/ai/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${AUTH_TOKEN}`
            },
            body: JSON.stringify({
                message: monitoringPrompt,
                conversation_id: `chat-monitor-${currentUser.id}`,
                model: selectedModel
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
                displayAIMessage(data.response, data.tools_used, data.metrics);
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
    console.log('[AI] Toggle clicked, current state:', isAIActive);
    
    // Toggle the state
    isAIActive = !isAIActive;
    isListening = isAIActive;
    
    const toggleBtn = document.getElementById('ai-toggle');
    const toggleText = toggleBtn?.querySelector('.ai-toggle-text');
    const listeningIndicator = document.getElementById('ai-listening-indicator');
    
    if (isAIActive) {
        // Turn AI ON
        console.log('🤖 AI monitoring enabled');
        if (toggleBtn) toggleBtn.classList.add('active');
        if (toggleText) toggleText.textContent = 'AI On';
        if (listeningIndicator) listeningIndicator.classList.add('active');
        
        startPassiveListening();
        localStorage.setItem('aiAssistantEnabled', 'true');
        
        displaySystemMessage(
            '🤖 AI monitoring enabled - I\'ll provide insights and suggestions as you chat.',
            'info-message'
        );
    } else {
        // Turn AI OFF
        console.log('🤖 AI monitoring disabled');
        if (toggleBtn) toggleBtn.classList.remove('active');
        if (toggleText) toggleText.textContent = 'AI Off';
        if (listeningIndicator) listeningIndicator.classList.remove('active');
        
        stopPassiveListening();
        localStorage.setItem('aiAssistantEnabled', 'false');
        
        displaySystemMessage(
            '🤖 AI monitoring disabled - Use /ai command or AI button for direct questions.',
            'info-message'
        );
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
        // Get selected LLM model from dropdown
        const selectedModel = window.getCurrentLLMModel ? window.getCurrentLLMModel() : 'gpt-4o-mini';
        console.log('[AI] Using model:', selectedModel);
        
        // Check if local LLM is enabled - use it if enabled, regardless of model name in dropdown
        // The localLLM.settings.model will contain the actual local model name (e.g., "ibm/granite-4-h-tiny")
        const useLocalLLM = localLLM.settings.enabled;
        
        let responseText = '';
        let toolsUsed = [];
        
        if (useLocalLLM) {
            // Try local LLM first
            console.log('[AI] 🏠 Attempting local LLM connection...');
            console.log('[AI] 🏠 Local LLM settings:', localLLM.settings);
            try {
                const available = await localLLM.checkAvailability();
                if (available) {
                    console.log('[AI] ✅ Local LLM available, sending request...');
                    // Use the model from local LLM settings, not the dropdown
                    const localModel = localLLM.settings.model || 'local-model';
                    console.log('[AI] 🏠 Using local model:', localModel);
                    const messages = [
                        { role: 'system', content: 'You are a helpful AI assistant for Socializer, a social skills training app. Be friendly and supportive.' },
                        { role: 'user', content: aiPrompt }
                    ];
                    const result = await localLLM.chat(messages, { model: localModel });
                    responseText = result.content;
                    toolsUsed = ['local_llm'];
                    console.log('[AI] ✅ Local LLM response received');
                } else {
                    throw new Error('Local LLM not available');
                }
            } catch (localError) {
                console.warn('[AI] ⚠️ Local LLM failed, falling back to cloud:', localError.message);
                // Fall through to cloud API
            }
        }
        
        // Use cloud API if local didn't work or wasn't enabled
        if (!responseText) {
            console.log('[AI] ☁️ Using cloud API...');
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${AUTH_TOKEN}`
                },
                body: JSON.stringify({
                    message: aiPrompt,
                    conversation_id: `chat-${currentUser.id}`,
                    model: selectedModel
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('[AI] Response data:', data);
                responseText = data.response;
                toolsUsed = data.tools_used || [];
            } else {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Unknown error');
            }
        }
        
        hideAITypingIndicator();
        displayAIMessage(responseText, toolsUsed);
        
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

function displayAIMessage(text, tools = null, metrics = null) {
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
        // Parse markdown for AI responses - this renders code blocks, lists, etc.
        const parsedContent = parseMarkdown(text);
        contentDiv.innerHTML = `<strong>🤖 AI Assistant:</strong><br>${parsedContent}`;
        console.log('[AI] ✅ Content HTML set with markdown parsing');
    } catch (error) {
        console.error('[AI] ❌ Error parsing markdown:', error);
        // Fallback to escaped HTML if markdown parsing fails
        contentDiv.innerHTML = `<strong>🤖 AI Assistant:</strong><br>${escapeHtml(text)}`;
    }
    
    // Display tools used
    if (tools && tools.length > 0) {
        const toolsInfo = document.createElement('div');
        toolsInfo.style.fontSize = '0.75rem';
        toolsInfo.style.marginTop = '0.5rem';
        toolsInfo.style.opacity = '0.8';
        toolsInfo.innerHTML = `<i class="bi bi-tools"></i> Tools: ${tools.join(', ')}`;
        contentDiv.appendChild(toolsInfo);
        console.log('[AI] ✅ Tools info added');
    }
    
    // Display metrics (optional)
    if (metrics) {
        const metricsInfo = document.createElement('div');
        metricsInfo.style.fontSize = '0.7rem';
        metricsInfo.style.marginTop = '0.25rem';
        metricsInfo.style.opacity = '0.6';
        const parts = [];
        if (metrics.total_tokens) parts.push(`${metrics.total_tokens} tokens`);
        if (metrics.cost_usd) parts.push(`$${metrics.cost_usd.toFixed(4)}`);
        if (parts.length > 0) {
            metricsInfo.innerHTML = `<i class="bi bi-graph-up"></i> ${parts.join(' • ')}`;
            contentDiv.appendChild(metricsInfo);
            console.log('[AI] ✅ Metrics info added');
        }
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
            
        case 'chat_history':
            // Display historical messages when joining
            console.log('[CHAT HISTORY] Received chat history:', message);
            console.log('[CHAT HISTORY] Number of messages:', message.messages ? message.messages.length : 0);
            
            if (message.messages && Array.isArray(message.messages) && message.messages.length > 0) {
                console.log('[CHAT HISTORY] Processing', message.messages.length, 'historical messages');
                // Display a separator for history
                const historyMarker = document.createElement('div');
                historyMarker.className = 'message system-message';
                historyMarker.innerHTML = `
                    <div class="message-content">
                        <i class="bi bi-clock-history"></i>
                        Previous messages (last 10)
                    </div>
                `;
                elements.chatMessages.appendChild(historyMarker);
                
                // Display each historical message
                message.messages.forEach(msg => {
                    displayMessage({
                        sender: {
                            id: msg.user_id,
                            username: msg.username
                        },
                        content: msg.content,
                        timestamp: msg.timestamp,
                        messageType: 'chat_message',
                        isHistory: true  // Mark as historical
                    });
                });
                
                // Add end of history marker
                const endMarker = document.createElement('div');
                endMarker.className = 'message system-message';
                endMarker.innerHTML = `
                    <div class="message-content">
                        <i class="bi bi-arrow-down-circle"></i>
                        New messages below
                    </div>
                `;
                elements.chatMessages.appendChild(endMarker);
                
                // Scroll to bottom
                elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
            }
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

/**
 * Parse markdown content to HTML using marked.js
 * @param {string} content - Raw markdown content
 * @returns {string} - Parsed HTML
 */
function parseMarkdown(content) {
    if (typeof marked === 'undefined') {
        console.warn('Marked.js not loaded, returning plain content');
        return escapeHtml(content);
    }
    
    try {
        // Configure marked for security and proper rendering
        marked.setOptions({
            breaks: true,          // Convert \n to <br>
            gfm: true,            // GitHub Flavored Markdown
            headerIds: false,     // Don't add IDs to headers
            mangle: false,        // Don't escape emails
            sanitize: false,      // We'll handle XSS ourselves
        });
        
        return marked.parse(content);
    } catch (error) {
        console.error('Error parsing markdown:', error);
        return escapeHtml(content);
    }
}

/**
 * Check if a message should be rendered as markdown
 * @param {string} sender - Message sender
 * @param {string} messageType - Type of message
 * @returns {boolean}
 */
function shouldUseMarkdown(sender, messageType) {
    // Use markdown for AI assistant messages
    const senderName = (sender.username || sender || '').toLowerCase();
    return senderName.includes('assistant') || 
           senderName.includes('ai') || 
           messageType === 'ai_message' ||
           messageType === 'ai-suggestion';
}

function displayMessage({ sender, content, messageType = 'chat_message', timestamp, isHistory = false }) {
    if (!elements.chatMessages) return;
    
    const messageElement = document.createElement('div');
    messageElement.className = `message ${messageType}${isHistory ? ' history-message' : ''}`;
    
    const timeString = formatTime(timestamp);
    
    // Determine if we should parse markdown
    const useMarkdown = shouldUseMarkdown(sender, messageType);
    const processedContent = useMarkdown ? parseMarkdown(content) : escapeHtml(content);
    
    messageElement.innerHTML = `
        <div class="message-header">
            <span class="sender" style="color: ${getUserColor(sender.id || sender)}">
                ${escapeHtml(sender.username || sender)}
            </span>
            <span class="time">${timeString}</span>
            ${isHistory ? '<span class="history-badge">history</span>' : ''}
        </div>
        <div class="message-content">${processedContent}</div>
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

async function setupEventListeners() {
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
    

    // Initialize private rooms manager
    console.log('[CHAT] Initializing private rooms manager...');
    try {
        await privateRoomsManager.init();
        
        // Set callback for when a room is selected
        privateRoomsManager.onRoomSelected = (room) => {
            console.log('[CHAT] Room selected callback:', room);
            
            // Check if going back to main
            if (room.is_main) {
                currentRoom = CHAT_ROOM;
                currentUser.room = currentRoom;
                console.log(`[TRACE] Switched back to main chat`);
                
                const currentRoomEl = document.getElementById('current-room');
                const roomDescEl = document.getElementById('room-description');
                
                if (currentRoomEl) {
                    currentRoomEl.textContent = 'General Chat';
                }
                
                if (roomDescEl) {
                    roomDescEl.textContent = 'Everyone can join this chat';
                }
                
                // Notify WebSocket of room change
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        type: 'join_room',
                        room_id: 'general',
                        timestamp: new Date().toISOString()
                    }));
                }
                
                return;
            }
            
            // SWITCH TO PRIVATE ROOM
            currentRoom = `room_${room.id}`;
            currentUser.room = currentRoom;
            
            console.log(`[TRACE] Switched to room: ${currentRoom}`);
            
            // Update UI
            const currentRoomEl = document.getElementById('current-room');
            const roomDescEl = document.getElementById('room-description');
            
            if (currentRoomEl) {
                currentRoomEl.textContent = room.name || `Room #${room.id}`;
            }
            
            if (roomDescEl) {
                let desc = `${room.member_count || 0} members`;
                if (room.password) desc += ' • 🔒 Protected';
                if (room.ai_enabled) desc += ' • 🤖 AI Active';
                roomDescEl.textContent = desc;
            }
            
            // Notify WebSocket of room change
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({
                    type: 'join_room',
                    room_id: currentRoom,
                    timestamp: new Date().toISOString()
                }));
                console.log(`[TRACE] Sent join_room message for ${currentRoom}`);
            }
            
            // Clear messages and load room history
            if (elements.chatMessages) {
                elements.chatMessages.innerHTML = `
                    <div class="message system-message">
                        <div class="message-content">
                            <i class="bi bi-door-open"></i>
                            Switched to ${room.name || 'private room'}. Loading message history...
                        </div>
                    </div>
                `;
            }
            
            // Load last 10 messages from this room
            loadRoomMessageHistory(room.id);
        };
        
        console.log('[CHAT] Private rooms manager initialized successfully');
    } catch (error) {
        console.error('[ERROR] Failed to initialize private rooms:', error);
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
            e.preventDefault();
            console.log('[CHAT] Logout button clicked!');
            handleLogout();
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
        
        await setupEventListeners();
        
        // Initialize AI state from localStorage (user preference)
        const aiEnabled = localStorage.getItem('aiAssistantEnabled') === 'true';
        console.log('🤖 AI monitoring state from localStorage:', aiEnabled);
        
        const toggleBtn = document.getElementById('ai-toggle');
        const toggleText = toggleBtn?.querySelector('.ai-toggle-text');
        const listeningIndicator = document.getElementById('ai-listening-indicator');
        
        // Set AI state based on user preference
        isAIActive = aiEnabled;
        isListening = aiEnabled;
        
        if (toggleBtn && toggleText) {
            toggleBtn.disabled = false;  // Enable toggle button
            toggleBtn.title = 'Toggle AI passive listening';
            
            if (aiEnabled) {
                toggleBtn.classList.add('active');
                toggleText.textContent = 'AI On';
                if (listeningIndicator) listeningIndicator.classList.add('active');
                startPassiveListening();
                console.log('🤖 AI passive listening enabled (user preference)');
            } else {
                toggleBtn.classList.remove('active');
                toggleText.textContent = 'AI Off';
                if (listeningIndicator) listeningIndicator.classList.remove('active');
                console.log('🤖 AI passive listening disabled (user preference)');
            }
        }
        
        await initWebSocket();
        console.log('Chat application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize chat application:', error);
        updateConnectionStatus(false, 'Failed to connect');
    }
}

// Load room message history
async function loadRoomMessageHistory(roomId) {
    console.log('🔵 [HISTORY] ========== START LOADING MESSAGE HISTORY ==========');
    console.log('🔵 [HISTORY] Room ID:', roomId);
    console.log('🔵 [HISTORY] Current room:', currentRoom);
    console.log('🔵 [HISTORY] Current user:', currentUser);
    console.log('🔵 [HISTORY] elements.chatMessages exists:', !!elements.chatMessages);
    
    try {
        // Check all token sources
        console.log('🔵 [HISTORY] Checking token sources:');
        console.log('  - window.currentUser?.token:', !!window.currentUser?.token);
        console.log('  - window.ACCESS_TOKEN:', !!window.ACCESS_TOKEN);
        console.log('  - localStorage.access_token:', !!localStorage.getItem('access_token'));
        
        // Use same token retrieval as PrivateRooms
        const token = window.currentUser?.token || window.ACCESS_TOKEN || localStorage.getItem('access_token');
        if (!token) {
            console.error('🔴 [HISTORY] ERROR: No token found, cannot load messages');
            console.error('🔴 [HISTORY] Checked all three sources - all returned null/undefined');
            return;
        }
        
        console.log('🟢 [HISTORY] Token found! Length:', token.length);
        console.log('🟢 [HISTORY] Token starts with:', token.substring(0, 20) + '...');
        
        const url = `/api/rooms/${roomId}/messages?limit=10`;
        console.log('🔵 [HISTORY] Fetching from URL:', url);
        console.log('🔵 [HISTORY] About to call fetch...');
        
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });
        
        console.log('🟢 [HISTORY] Fetch completed!');
        console.log('🟢 [HISTORY] Response status:', response.status);
        console.log('🟢 [HISTORY] Response ok:', response.ok);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[ERROR] API error:', { status: response.status, text: errorText });
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const messages = await response.json();
        console.log('[TRACE] Loaded message history:', { count: messages.length, messages });
        console.log('[TRACE] First message from API:', messages[0]);
        console.log('[TRACE] Last message from API:', messages[messages.length - 1]);
        
        // Don't reverse - API already returns in correct order (oldest first)
        const messagesReversed = messages; // No reverse needed
        console.log('[TRACE] After reverse - first message:', messagesReversed[0]);
        console.log('[TRACE] After reverse - last message:', messagesReversed[messagesReversed.length - 1]);
        
        // Clear the "Loading..." message
        if (elements.chatMessages) {
            elements.chatMessages.innerHTML = '';
        }
        
        if (messagesReversed.length === 0) {
            // No message history
            if (elements.chatMessages) {
                elements.chatMessages.innerHTML = `
                    <div class="message system-message">
                        <div class="message-content">
                            <i class="bi bi-chat-dots"></i>
                            No message history. Be the first to say something!
                        </div>
                    </div>
                `;
            }
        } else {
            // Show info message about history
            if (elements.chatMessages) {
                elements.chatMessages.innerHTML = `
                    <div class="message system-message">
                        <div class="message-content">
                            <i class="bi bi-clock-history"></i>
                            Showing last ${messagesReversed.length} message${messagesReversed.length > 1 ? 's' : ''}
                        </div>
                    </div>
                `;
            }
            
            // Display each message
            messagesReversed.forEach(msg => {
                displayRoomMessage(msg);
            });
        }
        
        // Scroll to bottom
        if (elements.chatMessages) {
            elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        }
        
    } catch (error) {
        console.error('[ERROR] Failed to load message history:', error);
        if (elements.chatMessages) {
            elements.chatMessages.innerHTML += `
                <div class="message system-message">
                    <div class="message-content">
                        <i class="bi bi-exclamation-triangle"></i>
                        Failed to load message history
                    </div>
                </div>
            `;
        }
    }
}

// Display a room message in the UI
function displayRoomMessage(msg) {
    console.log('[TRACE] displayRoomMessage called:', msg);
    
    if (!elements.chatMessages) {
        console.error('[ERROR] elements.chatMessages not found');
        return;
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message');
    
    // Determine message type
    if (msg.sender_type === 'ai') {
        messageDiv.classList.add('ai-message');
    } else if (msg.sender_id === currentUser?.id) {
        messageDiv.classList.add('sent');
    } else {
        messageDiv.classList.add('received');
    }
    
    // Format timestamp
    const timestamp = new Date(msg.created_at);
    const timeStr = timestamp.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
    
    // Build message HTML
    const senderName = msg.sender_username || 'Unknown';
    const isOwnMessage = msg.sender_id === currentUser?.id;
    
    messageDiv.innerHTML = `
        <div class="message-header">
            <span class="sender-name">${senderName}</span>
            <span class="message-time">${timeStr}</span>
        </div>
        <div class="message-content">${escapeHtml(msg.content)}</div>
    `;
    
    console.log('[TRACE] Appending message to DOM');
    elements.chatMessages.appendChild(messageDiv);
}

// Logout handler
function handleLogout() {
    console.log('[TRACE] Logout initiated');
    
    // Close WebSocket connection
    closeWebSocket();
    
    // Clear localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('aiAssistantEnabled');
    
    // Redirect to login
    window.location.href = '/login';
}

// TEST FUNCTION - Call this manually from console
window.testMessageHistory = function(roomId) {
    console.log('🧪 [TEST] Manual test of message history for room:', roomId);
    loadRoomMessageHistory(roomId);
};

console.log('💡 TIP: Test message history manually with: testMessageHistory(26)');


// ==================== LLM Configuration Management ====================

/**
 * LLMConfigManager - Manages Local LLM Configuration
 * 
 * Handles CRUD operations for user's custom LLM settings including
 * provider selection, endpoint configuration (IP/port), and model name.
 * Follows OOP principles with clear separation of concerns.
 */
class LLMConfigManager {
    /**
     * Initialize the LLM configuration manager
     */
    constructor() {
        this.apiBaseUrl = '/api/ai/llm-config';
        this.modal = null;
        this.form = null;
        this.initialized = false;
    }

    /**
     * Initialize event listeners and load current configuration
     */
    async initialize() {
        if (this.initialized) return;
        
        console.log('[LLM Config] Initializing LLM configuration manager');
        
        // Get modal and form elements
        this.modal = document.getElementById('llmConfigModal');
        this.form = document.getElementById('llm-config-form');
        
        if (!this.modal || !this.form) {
            console.warn('[LLM Config] Modal or form not found');
            return;
        }

        // Setup event listeners
        this._setupEventListeners();
        
        // Load current configuration when modal is opened
        this.modal.addEventListener('show.bs.modal', () => {
            this.loadConfiguration();
        });
        
        this.initialized = true;
        console.log('[LLM Config] Initialization complete');
    }

    /**
     * Setup event listeners for form interactions
     * @private
     */
    _setupEventListeners() {
        const saveBtn = document.getElementById('save-llm-config-btn');
        const clearBtn = document.getElementById('clear-llm-config-btn');
        const ipInput = document.getElementById('llm-ip');
        const portInput = document.getElementById('llm-port');
        const providerSelect = document.getElementById('llm-provider');

        // Save configuration
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveConfiguration());
        }

        // Clear configuration
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearConfiguration());
        }

        // Update endpoint preview when inputs change
        const updatePreview = () => this._updateEndpointPreview();
        if (ipInput) ipInput.addEventListener('input', updatePreview);
        if (portInput) portInput.addEventListener('input', updatePreview);

        // Update port placeholder based on provider selection
        if (providerSelect) {
            providerSelect.addEventListener('change', (e) => {
                this._updateProviderDefaults(e.target.value);
            });
        }
    }

    /**
     * Update endpoint preview display
     * @private
     */
    _updateEndpointPreview() {
        const ip = document.getElementById('llm-ip')?.value || 'localhost';
        const port = document.getElementById('llm-port')?.value || '1234';
        const preview = document.getElementById('endpoint-preview');
        
        if (preview) {
            preview.textContent = `http://${ip}:${port}`;
        }
    }

    /**
     * Update default values based on selected provider
     * @private
     * @param {string} provider - Selected provider name
     */
    _updateProviderDefaults(provider) {
        const portInput = document.getElementById('llm-port');
        const modelInput = document.getElementById('llm-model');
        
        // Set default ports and model hints based on provider
        const defaults = {
            'lm_studio': { port: '1234', model: 'local-model' },
            'ollama': { port: '11434', model: 'llama3.2' },
            'openai': { port: '443', model: 'gpt-4o-mini' },
            'gemini': { port: '443', model: 'gemini-2.0-flash-exp' },
            'claude': { port: '443', model: 'claude-sonnet-4-0' }
        };

        const config = defaults[provider];
        if (config) {
            if (portInput) portInput.placeholder = config.port;
            if (modelInput) modelInput.placeholder = config.model;
        }

        this._updateEndpointPreview();
    }

    /**
     * Load current LLM configuration from server
     * @returns {Promise<void>}
     */
    async loadConfiguration() {
        try {
            console.log('[LLM Config] Loading configuration...');
            this._showStatus('Loading configuration...', 'info');

            const response = await this._makeAuthenticatedRequest('GET', this.apiBaseUrl);
            
            if (response.ok) {
                const config = await response.json();
                console.log('[LLM Config] Configuration loaded:', config);
                
                // Populate form with loaded configuration
                this._populateForm(config);
                this._showStatus('Configuration loaded successfully', 'success', 2000);
            } else {
                throw new Error(`Failed to load configuration: ${response.status}`);
            }
        } catch (error) {
            console.error('[LLM Config] Error loading configuration:', error);
            this._showStatus('Failed to load configuration', 'danger');
        }
    }

    /**
     * Save LLM configuration to server
     * @returns {Promise<void>}
     */
    async saveConfiguration() {
        try {
            // Validate form
            if (!this.form.checkValidity()) {
                this.form.reportValidity();
                return;
            }

            console.log('[LLM Config] Saving configuration...');
            this._showStatus('Saving configuration...', 'info');

            const config = this._getFormData();
            
            const response = await this._makeAuthenticatedRequest(
                'POST',
                this.apiBaseUrl,
                config
            );

            if (response.ok) {
                const result = await response.json();
                console.log('[LLM Config] Configuration saved:', result);
                this._showStatus('Configuration saved successfully!', 'success', 3000);
                
                // Close modal after successful save
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(this.modal);
                    if (modal) modal.hide();
                }, 1500);
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save configuration');
            }
        } catch (error) {
            console.error('[LLM Config] Error saving configuration:', error);
            this._showStatus(`Error: ${error.message}`, 'danger');
        }
    }

    /**
     * Clear LLM configuration
     * @returns {Promise<void>}
     */
    async clearConfiguration() {
        try {
            if (!confirm('Are you sure you want to clear your LLM configuration?')) {
                return;
            }

            console.log('[LLM Config] Clearing configuration...');
            this._showStatus('Clearing configuration...', 'info');

            const response = await this._makeAuthenticatedRequest('DELETE', this.apiBaseUrl);

            if (response.ok) {
                console.log('[LLM Config] Configuration cleared');
                this._showStatus('Configuration cleared successfully!', 'success', 3000);
                
                // Clear form
                this._clearForm();
                
                // Close modal after successful clear
                setTimeout(() => {
                    const modal = bootstrap.Modal.getInstance(this.modal);
                    if (modal) modal.hide();
                }, 1500);
            } else {
                throw new Error('Failed to clear configuration');
            }
        } catch (error) {
            console.error('[LLM Config] Error clearing configuration:', error);
            this._showStatus(`Error: ${error.message}`, 'danger');
        }
    }

    /**
     * Get form data as configuration object
     * @private
     * @returns {Object} Configuration data
     */
    _getFormData() {
        const ip = document.getElementById('llm-ip').value.trim();
        const port = document.getElementById('llm-port').value.trim();
        const provider = document.getElementById('llm-provider').value;
        const model = document.getElementById('llm-model').value.trim();

        return {
            provider: provider || null,
            endpoint: (ip && port) ? `http://${ip}:${port}` : null,
            model: model || null
        };
    }

    /**
     * Populate form with configuration data
     * @private
     * @param {Object} config - Configuration data
     */
    _populateForm(config) {
        // Set provider
        const providerSelect = document.getElementById('llm-provider');
        if (providerSelect && config.provider) {
            providerSelect.value = config.provider;
            this._updateProviderDefaults(config.provider);
        }

        // Parse and set endpoint (IP and port)
        if (config.endpoint) {
            try {
                const url = new URL(config.endpoint);
                const ipInput = document.getElementById('llm-ip');
                const portInput = document.getElementById('llm-port');
                
                if (ipInput) ipInput.value = url.hostname;
                if (portInput) portInput.value = url.port || '80';
            } catch (e) {
                console.warn('[LLM Config] Invalid endpoint URL:', config.endpoint);
            }
        }

        // Set model
        const modelInput = document.getElementById('llm-model');
        if (modelInput && config.model) {
            modelInput.value = config.model;
        }

        this._updateEndpointPreview();
    }

    /**
     * Clear all form fields
     * @private
     */
    _clearForm() {
        if (this.form) this.form.reset();
        this._updateEndpointPreview();
    }

    /**
     * Show status message in modal
     * @private
     * @param {string} message - Status message
     * @param {string} type - Alert type (success, danger, info, warning)
     * @param {number} [duration] - Auto-hide duration in milliseconds
     */
    _showStatus(message, type, duration = null) {
        const statusDiv = document.getElementById('llm-config-status');
        if (!statusDiv) return;

        statusDiv.className = `alert alert-${type}`;
        statusDiv.textContent = message;
        statusDiv.style.display = 'block';

        if (duration) {
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, duration);
        }
    }

    /**
     * Make authenticated API request
     * @private
     * @param {string} method - HTTP method
     * @param {string} url - Request URL
     * @param {Object} [data] - Request body data
     * @returns {Promise<Response>}
     */
    async _makeAuthenticatedRequest(method, url, data = null) {
        // Use the same token retrieval as the rest of the app
        const token = getAuthToken();
        
        if (!token) {
            console.error('[LLM Config] No authentication token found');
            throw new Error('Authentication required. Please log in.');
        }
        
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        return fetch(url, options);
    }
}

// Initialize LLM configuration manager
const llmConfigManager = new LLMConfigManager();

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    llmConfigManager.initialize().catch(console.error);
});


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
