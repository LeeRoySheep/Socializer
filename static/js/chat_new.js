// Chat class to manage WebSocket connection and message handling
class Chat {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second delay
        this.messageQueue = [];
        
        // Bind methods
        this.init = this.init.bind(this);
        this.connect = this.connect.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.handleMessage = this.handleMessage.bind(this);
        this.handleDisconnect = this.handleDisconnect.bind(this);
        this.handleError = this.handleError.bind(this);
        this.addMessageToUI = this.addMessageToUI.bind(this);
    }

    // Initialize the chat
    init() {
        this.setupEventListeners();
        this.connect();
    }

    // Set up WebSocket connection
    connect() {
        try {
            const wsScheme = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
            const wsUrl = `${wsScheme}${window.location.host}/ws/chat?token=${encodeURIComponent(window.ACCESS_TOKEN || '')}`;
            
            console.log('Connecting to WebSocket:', wsUrl);
            this.socket = new WebSocket(wsUrl);
            
            // Set up event handlers
            this.socket.onopen = () => {
                console.log('WebSocket connection established');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus(true);
                
                // Process any queued messages
                this.processMessageQueue();
            };
            
            this.socket.onmessage = this.handleMessage;
            this.socket.onclose = this.handleDisconnect;
            this.socket.onerror = this.handleError;
            
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.handleError(error);
        }
    }

    // Handle incoming messages
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);
            
            switch (data.type) {
                case 'chat_message':
                case 'ai_message':
                    this.addMessageToUI(data.sender, data.message, data.sender === (window.USER_DATA?.username || 'You'));
                    break;
                    
                case 'user_list':
                    this.updateOnlineUsers(data.users || []);
                    break;
                    
                case 'user_joined':
                    if (data.username && data.username !== window.USER_DATA?.username) {
                        this.addMessageToUI('System', `${data.username} has joined the chat`);
                    }
                    break;
                    
                case 'user_left':
                    if (data.username && data.username !== window.USER_DATA?.username) {
                        this.addMessageToUI('System', `${data.username} has left the chat`);
                    }
                    break;
                    
                case 'error':
                    console.error('Server error:', data.message);
                    this.addMessageToUI('System', `Error: ${data.message}`);
                    
                    if (data.message && (data.message.includes('token') || data.message.includes('auth'))) {
                        window.location.href = '/login?error=session_expired';
                    }
                    break;
                    
                default:
                    console.log('Unhandled message type:', data.type, data);
            }
        } catch (error) {
            console.error('Error processing message:', error, 'Raw data:', event.data);
        }
    }

    // Send a chat message
    async sendMessage(message) {
        const trimmedMessage = message.trim();
        if (!trimmedMessage) return false;
        
        const messageData = {
            type: 'chat_message',
            sender: window.USER_DATA?.username || 'Unknown',
            message: trimmedMessage,
            timestamp: new Date().toISOString()
        };
        
        if (this.isConnected && this.socket.readyState === WebSocket.OPEN) {
            try {
                this.socket.send(JSON.stringify(messageData));
                this.addMessageToUI('You', trimmedMessage, true);
                return true;
            } catch (error) {
                console.error('Error sending message:', error);
                this.addMessageToUI('System', 'Failed to send message. Please try again.');
                return false;
            }
        } else {
            // Queue the message if not connected
            this.messageQueue.push(messageData);
            this.addMessageToUI('System', 'Not connected. Message will be sent when connection is restored.');
            this.connect(); // Try to reconnect
            return false;
        }
    }

    // Process any queued messages
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.socket.send(JSON.stringify(message));
        }
    }

    // Handle disconnection
    handleDisconnect(event) {
        console.log('WebSocket disconnected:', event);
        this.isConnected = false;
        this.updateConnectionStatus(false);
        
        // Try to reconnect if we haven't exceeded max attempts
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts);
            console.log(`Attempting to reconnect in ${delay}ms...`);
            
            setTimeout(() => {
                this.reconnectAttempts++;
                this.connect();
            }, delay);
        } else {
            this.addMessageToUI('System', 'Connection lost. Please refresh the page to reconnect.');
        }
    }

    // Handle WebSocket errors
    handleError(error) {
        console.error('WebSocket error:', error);
        this.isConnected = false;
        this.updateConnectionStatus(false);
    }

    // Update connection status in the UI
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.textContent = connected ? 'Connected' : 'Disconnected';
            statusElement.className = `badge rounded-pill ${connected ? 'bg-success' : 'bg-danger'}`;
        }
    }

    // Update online users list
    updateOnlineUsers(users) {
        const usersList = document.getElementById('online-users');
        if (!usersList) return;
        
        // Clear current list
        usersList.innerHTML = '';
        
        // Add each user to the list
        users.forEach(user => {
            const userElement = document.createElement('li');
            userElement.className = 'list-group-item d-flex justify-content-between align-items-center';
            userElement.innerHTML = `
                ${user.username}
                <span class="badge bg-primary rounded-pill">${user.status || 'online'}</span>
            `;
            usersList.appendChild(userElement);
        });
    }

    // Add message to the chat UI
    addMessageToUI(sender, message, isCurrentUser = false) {
        const messagesContainer = document.getElementById('chat-messages');
        if (!messagesContainer) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${isCurrentUser ? 'user-message' : 'other-message'}`;
        
        messageElement.innerHTML = `
            <div class="message-sender">${sender}</div>
            <div class="message-content">${message}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Set up event listeners for the chat UI
    setupEventListeners() {
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-btn');
        
        if (!messageInput || !sendButton) {
            console.error('Could not find message input or send button');
            return;
        }
        
        // Handle send button click
        sendButton.addEventListener('click', () => {
            const message = messageInput.value.trim();
            if (message) {
                this.sendMessage(message);
                messageInput.value = '';
                messageInput.focus();
            }
        });
        
        // Handle Enter key to send message (Shift+Enter for new line)
        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const message = messageInput.value.trim();
                if (message) {
                    this.sendMessage(message);
                    messageInput.value = '';
                }
            }
        });
        
        // Auto-resize textarea as user types
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
        
        // Focus the input field when the page loads
        messageInput.focus();
    }
}

// Initialize chat when the page loads
document.addEventListener('DOMContentLoaded', () => {
    console.log('Initializing chat...');
    window.chat = new Chat();
    window.chat.init();
});
