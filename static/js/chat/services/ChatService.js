export class ChatService {
    constructor() {
        this.socket = null;
        this.messageHandlers = [];
        this.userListHandlers = [];
        this.typingHandlers = [];
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000; // 3 seconds
        this.pingInterval = null;
        this.isConnected = false;
    }

    async initialize({ onMessage, onUserListUpdate, onTyping }) {
        // Register event handlers
        if (onMessage) this.onMessage(onMessage);
        if (onUserListUpdate) this.onUserListUpdate(onUserListUpdate);
        if (onTyping) this.onTyping(onTyping);

        // Connect to WebSocket
        await this.connect();
    }

    onMessage(handler) {
        this.messageHandlers.push(handler);
    }

    onUserListUpdate(handler) {
        this.userListHandlers.push(handler);
    }

    onTyping(handler) {
        this.typingHandlers.push(handler);
    }

    async connect() {
        return new Promise((resolve, reject) => {
            try {
                // Get the WebSocket URL (handles both http and https)
                const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
                const wsUrl = `${protocol}${window.location.host}/ws/chat`;
                
                this.socket = new WebSocket(wsUrl);

                this.socket.onopen = () => {
                    console.log('WebSocket connected');
                    this.isConnected = true;
                    this.reconnectAttempts = 0;
                    this.setupPing();
                    resolve();
                };

                this.socket.onmessage = (event) => {
                    this.handleMessage(event);
                };

                this.socket.onclose = () => {
                    console.log('WebSocket disconnected');
                    this.isConnected = false;
                    this.cleanup();
                    this.attemptReconnect();
                };

                this.socket.onerror = (error) => {
                    console.error('WebSocket error:', error);
                    this.isConnected = false;
                    reject(error);
                };

            } catch (error) {
                console.error('Failed to connect to WebSocket:', error);
                reject(error);
            }
        });
    }

    handleMessage(event) {
        try {
            const message = JSON.parse(event.data);
            console.log('Received message:', message);

            switch (message.type) {
                case 'message':
                    this.messageHandlers.forEach(handler => handler(message.data));
                    break;
                case 'user_list':
                    this.userListHandlers.forEach(handler => handler(message.data));
                    break;
                case 'typing':
                    this.typingHandlers.forEach(handler => handler(message.data));
                    break;
                case 'pong':
                    // Reset ping/pong check
                    this.lastPongTime = Date.now();
                    break;
                default:
                    console.warn('Unknown message type:', message.type);
            }
        } catch (error) {
            console.error('Error processing message:', error);
        }
    }

    async sendMessage(message) {
        if (!this.isConnected) {
            throw new Error('Not connected to chat server');
        }

        return new Promise((resolve, reject) => {
            try {
                this.socket.send(JSON.stringify({
                    type: 'message',
                    data: message
                }));
                resolve();
            } catch (error) {
                console.error('Failed to send message:', error);
                reject(error);
            }
        });
    }

    sendTyping(isTyping) {
        if (!this.isConnected) return;

        try {
            this.socket.send(JSON.stringify({
                type: 'typing',
                data: { isTyping }
            }));
        } catch (error) {
            console.error('Failed to send typing indicator:', error);
        }
    }

    async getMessages(limit = 50, before = null) {
        try {
            const params = new URLSearchParams({ limit });
            if (before) params.append('before', before);

            const response = await fetch(`/api/messages?${params}`);
            if (!response.ok) {
                throw new Error('Failed to fetch messages');
            }

            return await response.json();
        } catch (error) {
            console.error('Error fetching messages:', error);
            throw error;
        }
    }

    async getOnlineUsers() {
        try {
            const response = await fetch('/api/users/online');
            if (!response.ok) {
                throw new Error('Failed to fetch online users');
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching online users:', error);
            throw error;
        }
    }

    setupPing() {
        // Clear any existing interval
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }

        // Set up ping/pong to keep connection alive
        this.pingInterval = setInterval(() => {
            if (this.isConnected) {
                try {
                    this.socket.send(JSON.stringify({ type: 'ping' }));
                } catch (error) {
                    console.error('Error sending ping:', error);
                }
            }
        }, 30000); // Every 30 seconds
    }

    attemptReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            return;
        }

        this.reconnectAttempts++;
        const delay = this.reconnectDelay * this.reconnectAttempts;

        console.log(`Attempting to reconnect in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            this.connect().catch(error => {
                console.error('Reconnection failed:', error);
                this.attemptReconnect();
            });
        }, delay);
    }

    cleanup() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    }

    disconnect() {
        this.cleanup();
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
        this.isConnected = false;
    }
}

export default ChatService;
