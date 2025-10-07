/**
 * ChatController - Coordinates between WebSocketService, UserManager, and UIManager
 */
class ChatController {
    /**
     * Create a new ChatController
     * @param {Object} websocketService - Instance of WebSocketService
     * @param {Object} userManager - Instance of UserManager
     * @param {Object} uiManager - Instance of UIManager
     * @param {Object} config - Configuration object
     */
    constructor(websocketService, userManager, uiManager, config) {
        this.websocketService = websocketService;
        this.userManager = userManager;
        this.uiManager = uiManager;
        this.config = config;
        
        // Bind methods
        this._handleWebSocketOpen = this._handleWebSocketOpen.bind(this);
        this._handleWebSocketMessage = this._handleWebSocketMessage.bind(this);
        this._handleWebSocketClose = this._handleWebSocketClose.bind(this);
        this._handleWebSocketError = this._handleWebSocketError.bind(this);
        this._handleUIEvent = this._handleUIEvent.bind(this);
        
        // Initialize
        this._init();
    }

    /**
     * Initialize the chat controller
     * @private
     */
    _init() {
        // Set up WebSocket event handlers
        this.websocketService.on('open', this._handleWebSocketOpen);
        this.websocketService.on('message', this._handleWebSocketMessage);
        this.websocketService.on('close', this._handleWebSocketClose);
        this.websocketService.on('error', this._handleWebSocketError);
        
        // Set up UI event handler
        this.uiManager.onEvent = this._handleUIEvent;
        
        // Connect to WebSocket
        this._connect();
    }

    /**
     * Connect to the WebSocket server
     * @private
     */
    _connect() {
        // Set up WebSocket URL with query parameters
        const url = new URL(this.config.websocketUrl);
        url.searchParams.append('token', this.config.token || '');
        url.searchParams.append('room_id', this.config.roomId || 'default');
        
        // Update WebSocket URL and connect
        this.websocketService.url = url.toString();
        this.websocketService.connect();
        
        // Request online users list after connection is established
        this.websocketService.on('open', () => {
            this._requestOnlineUsers();
            
            // Set up periodic refresh of online users
            this._setupOnlineUsersRefresh();
        });
    }
    
    /**
     * Request the list of online users
     * @private
     */
    _requestOnlineUsers() {
        this.websocketService.send({
            type: 'get_online_users',
            request_id: `req_${Date.now()}`,
            timestamp: new Date().toISOString()
        });
    }
    
    /**
     * Set up periodic refresh of online users
     * @private
     */
    _setupOnlineUsersRefresh() {
        // Refresh online users every 30 seconds
        setInterval(() => {
            if (this.websocketService.isConnected) {
                this._requestOnlineUsers();
            }
        }, 30000);
    }

    /**
     * Handle WebSocket open event
     * @private
     */
    _handleWebSocketOpen() {
        const { currentUser, roomId } = this.config;
        
        // Send handshake message
        this.websocketService.send({
            type: 'handshake',
            user_id: currentUser.id,
            username: currentUser.username,
            room_id: roomId
        });
        
        // Update UI
        this.uiManager.updateConnectionStatus(true, 'Connected');
    }

    /**
     * Handle WebSocket message event
     * @param {Object} event - The received message
     * @private
     */
    _handleWebSocketMessage(event) {
        try {
            const message = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
            console.log('Received message:', message);

            // Handle different message types
            switch (message.type) {
                case 'welcome':
                    this._handleWelcomeMessage(message);
                    break;
                case 'chat':
                    this._handleChatMessage(message);
                    break;
                case 'user_joined':
                    this._handleUserJoined(message);
                    break;
                case 'user_left':
                    this._handleUserLeft(message);
                    break;
                case 'typing':
                    this._handleTypingIndicator(message);
                    break;
                case 'error':
                    this._handleErrorMessage(message);
                    break;
                case 'user_status':
                    this._handleUserStatusUpdate(message);
                    break;
                case 'online_users':
                    this._handleOnlineUsers(message);
                    break;
                case 'system_message':
                    this._handleSystemMessage(message);
                    break;
                case 'pong':
                    // Handle pong for latency calculation if needed
                    break;
                default:
                    console.warn('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error processing message:', error);
        }
    }

    /**
     * Handle chat message
     * @param {Object} message - The chat message
     * @private
     */
    _handleChatMessage(message) {
        // Add message to UI
        this.uiManager.addMessage({
            id: message.id || Date.now().toString(),
            user_id: message.user_id,
            username: message.username || 'Unknown',
            content: message.content,
            timestamp: message.timestamp || new Date().toISOString()
        });
    }

    /**
     * Handle online users list update
     * @param {Object} message - The online users message
     * @private
     */
    _handleOnlineUsers(message) {
        if (message.users && Array.isArray(message.users)) {
            // Update the online users list in the UI
            this.uiManager.updateOnlineUsers(message.users);
            
            // Also update the UserManager
            this.userManager.updateOnlineUsers(message.users);
        }
    }

    /**
     * Handle user joined event
     * @param {Object} message - The user joined message
     * @private
     */
    _handleUserJoined(message) {
        // Update UI to show user joined
        const username = message.username || `User ${message.user_id}`;
        this.uiManager.addSystemMessage(`${username} has joined the chat`, 'info');
        
        // Update user list
        this.userManager.updateOnlineUsers([{
            user_id: message.user_id,
            username: username,
            status: 'online',
            timestamp: message.timestamp || new Date().toISOString()
        }]);
    }

    /**
     * Handle user left event
     * @param {Object} message - The user left message
     * @private
     */
    _handleUserLeft(message) {
        if (!message.user_id) return;
        
        // Get username before removing user
        const user = this.userManager.getUser(message.user_id);
        const username = user ? user.username : `User ${message.user_id}`;
        
        // Update UI to show user left
        this.uiManager.addSystemMessage(`${username} has left the chat`, 'info');
        
        // Update user list
        this.userManager.updateOnlineUsers([{
            user_id: message.user_id,
            username: username,
            status: 'offline',
            timestamp: message.timestamp || new Date().toISOString()
        }]);
    }

    /**
     * Handle user status update
     * @param {Object} message - Status update message
     * @private
     */
    _handleUserStatusUpdate(message) {
        const user = this.userManager.getUser(message.user_id);
        const username = user ? user.username : message.username || `User ${message.user_id}`;
        
        // Update user status
        this.userManager.updateOnlineUsers([{
            user_id: message.user_id,
            username: username,
            status: message.status,
            timestamp: message.timestamp || new Date().toISOString()
        }]);
    }

    /**
     * Handle typing indicator
     * @param {Object} message - The typing message
     * @private
     */
    _handleTyping(message) {
        if (message.user_id === this.config.currentUser.id) return;
        
        const user = this.userManager.getUserById(message.user_id);
        if (user) {
            this.uiManager.showTypingIndicator(user.username);
            
            // Hide typing indicator after 3 seconds
            if (this.typingTimeout) {
                clearTimeout(this.typingTimeout);
            }
            
            this.typingTimeout = setTimeout(() => {
                this.uiManager.hideTypingIndicator();
            }, 3000);
        }
    }

    /**
     * Handle WebSocket close event
     * @param {Object} event - The close event
     * @private
     */
    _handleWebSocketClose(event) {
        let statusMessage = 'Disconnected';
        
        if (event.code === 1000) {
            statusMessage += ': Normal closure';
        } else if (event.code === 1001) {
            statusMessage += ': Going away';
        } else if (event.code === 1006) {
            statusMessage += ': Connection failed';
        } else {
            statusMessage += `: Code ${event.code}`;
        }
        
        if (event.reason) {
            statusMessage += ` (${event.reason})`;
        }
        
        // Update UI
        this.uiManager.updateConnectionStatus(false, statusMessage);
    }

    /**
     * Handle WebSocket error event
     * @param {Error} error - The error object
     * @private
     */
    _handleWebSocketError(error) {
        console.error('WebSocket error:', error);
        this.uiManager.updateConnectionStatus(false, `Error: ${error.message}`);
    }

    /**
     * Handle UI events
     * @param {string} event - The event name
     * @param {*} data - The event data
     * @private
     */
    _handleUIEvent(event, data) {
        switch (event) {
            case 'send_message':
                this._handleSendMessage(data);
                break;
                
            case 'typing':
                this._handleUserTyping();
                break;
                
            default:
                console.warn('Unknown UI event:', event);
        }
    }

    /**
     * Handle send message from UI
     * @param {string} content - The message content
     * @private
     */
    _handleSendMessage(content) {
        if (!content.trim()) return;
        
        const { currentUser, roomId } = this.config;
        
        // Send message through WebSocket
        this.websocketService.send({
            type: 'chat_message',
            content: content,
            room_id: roomId,
            user_id: currentUser.id,
            username: currentUser.username,
            timestamp: new Date().toISOString()
        });
        
        // Clear input
        this.uiManager.clearMessageInput();
    }

    /**
     * Handle user typing event
     * @private
     */
    _handleUserTyping() {
        const now = Date.now();
        
        // Throttle typing events to once every 2 seconds
        if (!this.lastTypingTime || now - this.lastTypingTime > 2000) {
            this.lastTypingTime = now;
            
            this.websocketService.send({
                type: 'typing',
                user_id: this.config.currentUser.id,
                room_id: this.config.roomId
            });
        }
    }

    /**
     * Start the ping-pong mechanism
     * @private
     */
    _startPingPong() {
        // Send ping every 25 seconds (server timeout is usually 30s)
        this.pingInterval = setInterval(() => {
            if (this.websocketService.isConnected()) {
                this.websocketService.send({ type: 'ping' });
                this.lastPingTime = Date.now();
                
                // Check if we missed a pong
                if (this.lastPongTime && this.lastPingTime - this.lastPongTime > 30000) {
                    console.warn('No pong received, reconnecting...');
                    this._reconnect();
                }
            }
        }, 25000);
    }

    /**
     * Reconnect to the WebSocket server
     * @private
     */
    _reconnect() {
        // Clear existing connection
        this.websocketService.disconnect();
        
        // Try to reconnect
        setTimeout(() => {
            this._connect();
        }, 1000);
    }

    /**
     * Clean up resources
     */
    destroy() {
        // Clear intervals and timeouts
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }
        
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        
        // Disconnect WebSocket
        this.websocketService.disconnect();
        
        // Remove event handlers
        this.websocketService.off('open', this._handleWebSocketOpen);
        this.websocketService.off('message', this._handleWebSocketMessage);
        this.websocketService.off('close', this._handleWebSocketClose);
        this.websocketService.off('error', this._handleWebSocketError);
        
        // Clear UI event handler
        this.uiManager.onEvent = null;
    }
}

export { ChatController };
export default ChatController;
