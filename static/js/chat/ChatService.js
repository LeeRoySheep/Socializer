/**
 * Chat Service
 * Handles WebSocket connection and chat message management
 */
class ChatService {
    constructor() {
        this.socket = null;
        this.messageHandlers = new Set();
        this.connectionPromise = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
    }

    /**
     * Connect to the WebSocket server
     * @param {string} token - JWT token for authentication
     * @returns {Promise<WebSocket>} Resolves when connected
     */
    async connect(token) {
        if (this.connectionPromise) {
            return this.connectionPromise;
        }

        this.connectionPromise = new Promise((resolve, reject) => {
            try {
                // Create WebSocket connection with token
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${wsProtocol}//${window.location.host}/ws/chat/main?token=${encodeURIComponent(token)}`;
                
                this.socket = new WebSocket(wsUrl);
                this.reconnectAttempts = 0;

                this.socket.onopen = () => {
                    console.log('WebSocket connection established');
                    this.reconnectDelay = 1000; // Reset reconnect delay on successful connection
                    resolve(this.socket);
                };

                this.socket.onmessage = (event) => {
                    try {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    } catch (error) {
                        console.error('Error parsing WebSocket message:', error);
                    }
                };

                this.socket.onclose = (event) => {
                    console.log('WebSocket connection closed:', event.code, event.reason);
                    this.connectionPromise = null;
                    
                    // Don't attempt to reconnect if closed normally
                    if (event.code === 1000) return;
                    
                    this.attemptReconnect(token);
                };

                this.socket.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    reject(error);
                };
            } catch (error) {
                console.error('Error creating WebSocket:', error);
                reject(error);
            }
        });

        return this.connectionPromise;
    }

    /**
     * Attempt to reconnect to the WebSocket server
     * @param {string} token - JWT token for reconnection
     */
    async attemptReconnect(token) {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            this.notifyHandlers({
                type: 'error',
                message: 'Connection lost. Please refresh the page to reconnect.'
            });
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), this.maxReconnectDelay);
        
        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect(token).catch(error => {
                console.error('Reconnection attempt failed:', error);
            });
        }, delay);
    }

    /**
     * Disconnect from the WebSocket server
     */
    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'User logged out');
            this.socket = null;
        }
        this.connectionPromise = null;
        this.reconnectAttempts = 0;
    }

    /**
     * Send a chat message
     * @param {string} message - The message to send
     * @param {string} conversationId - Optional conversation ID
     * @returns {Promise<Object>} The sent message
     */
    async sendMessage(message, conversationId = 'default') {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            throw new Error('WebSocket is not connected');
        }

        const messageData = {
            type: 'chat_message',
            message: message,
            conversation_id: conversationId,
            timestamp: new Date().toISOString()
        };

        this.socket.send(JSON.stringify(messageData));
        return messageData;
    }

    /**
     * Handle incoming WebSocket messages
     * @param {Object} message - The received message
     */
    handleMessage(message) {
        console.log('Received message:', message);
        this.notifyHandlers(message);
    }

    /**
     * Register a message handler
     * @param {Function} handler - Function to handle messages
     * @returns {Function} Unsubscribe function
     */
    onMessage(handler) {
        if (typeof handler !== 'function') {
            throw new Error('Handler must be a function');
        }

        this.messageHandlers.add(handler);

        // Return unsubscribe function
        return () => {
            this.messageHandlers.delete(handler);
        };
    }

    /**
     * Notify all registered handlers of a message
     * @param {Object} message - The message to send to handlers
     */
    notifyHandlers(message) {
        this.messageHandlers.forEach(handler => {
            try {
                handler(message);
            } catch (error) {
                console.error('Error in message handler:', error);
            }
        });
    }
}

// Export a singleton instance
export const chatService = new ChatService();
