/**
 * WebSocketService - Handles WebSocket connections and events
 */
class WebSocketService {
    /**
     * Create a new WebSocketService
     * @param {string} url - WebSocket server URL
     * @param {Object} options - Configuration options
     */
    constructor(url, options = {}) {
        this.url = url;
        this.socket = null;
        this.eventListeners = new Map();
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 5;
        this.reconnectInterval = options.reconnectInterval || 3000; // 3 seconds
        this.pingInterval = options.pingInterval || 25000; // 25 seconds
        this.pongTimeout = options.pongTimeout || 10000; // 10 seconds
        this.lastPingTime = 0;
        this.lastPongTime = 0;
        this.pingTimer = null;
        this.pongTimer = null;
        this.isConnected = false;
        this.autoReconnect = options.autoReconnect !== false; // Default to true
    }

    /**
     * Connect to the WebSocket server
     */
    connect() {
        if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
            console.log('[WebSocket] Connection already exists or is connecting');
            return;
        }

        try {
            console.log(`[WebSocket] Connecting to ${this.url}`);
            this.socket = new WebSocket(this.url);
            this._setupEventHandlers();
        } catch (error) {
            console.error('[WebSocket] Error creating WebSocket:', error);
            this._handleError(error);
            this._scheduleReconnect();
        }
    }

    /**
     * Set up WebSocket event handlers
     * @private
     */
    _setupEventHandlers() {
        this.socket.onopen = (event) => {
            console.log('[WebSocket] Connection established');
            this.isConnected = true;
            this.reconnectAttempts = 0; // Reset reconnect attempts on successful connection
            this._startPingPong();
            this._emit('open', event);
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this._handleIncomingMessage(data);
            } catch (error) {
                console.error('[WebSocket] Error parsing message:', error);
                this._emit('error', { type: 'parse_error', error });
            }
        };

        this.socket.onclose = (event) => {
            console.log(`[WebSocket] Connection closed: ${event.code} ${event.reason || 'No reason provided'}`);
            this.isConnected = false;
            this._stopPingPong();
            this._emit('close', event);

            // Attempt to reconnect if the connection was not closed intentionally
            if (this.autoReconnect && !event.wasClean) {
                this._scheduleReconnect();
            }
        };

        this.socket.onerror = (error) => {
            console.error('[WebSocket] Error:', error);
            this._handleError(error);
        };
    }

    /**
     * Handle incoming WebSocket messages
     * @param {Object} data - The parsed message data
     * @private
     */
    _handleIncomingMessage(data) {
        // Handle ping-pong messages
        if (data.type === 'pong') {
            this._handlePong(data);
            return;
        }

        // Emit the message to listeners
        this._emit('message', data);
    }

    /**
     * Start the ping-pong mechanism
     * @private
     */
    _startPingPong() {
        // Clear any existing timers
        this._stopPingPong();

        // Send initial ping
        this._sendPing();

        // Set up ping interval
        this.pingTimer = setInterval(() => {
            this._sendPing();
        }, this.pingInterval);
    }

    /**
     * Stop the ping-pong mechanism
     * @private
     */
    _stopPingPong() {
        if (this.pingTimer) {
            clearInterval(this.pingTimer);
            this.pingTimer = null;
        }
        
        if (this.pongTimer) {
            clearTimeout(this.pongTimer);
            this.pongTimer = null;
        }
    }

    /**
     * Send a ping message
     * @private
     */
    _sendPing() {
        if (!this.isConnected) return;

        this.lastPingTime = Date.now();
        this.send({ type: 'ping', timestamp: this.lastPingTime });

        // Set up pong timeout
        if (this.pongTimer) clearTimeout(this.pongTimer);
        
        this.pongTimer = setTimeout(() => {
            if (this.isConnected) {
                console.warn('[WebSocket] Pong timeout, server not responding');
                this._handlePongTimeout();
            }
        }, this.pongTimeout);
    }

    /**
     * Handle incoming pong message
     * @param {Object} data - Pong message data
     * @private
     */
    _handlePong(data) {
        if (this.pongTimer) {
            clearTimeout(this.pongTimer);
            this.pongTimer = null;
        }

        this.lastPongTime = Date.now();
        const latency = this.lastPongTime - data.timestamp;
        
        console.log(`[WebSocket] Pong received, latency: ${latency}ms`);
        this._emit('pong', { latency, timestamp: this.lastPongTime });
    }

    /**
     * Handle pong timeout
     * @private
     */
    _handlePongTimeout() {
        console.error('[WebSocket] Server did not respond to ping, reconnecting...');
        this._emit('error', { type: 'pong_timeout' });
        this.reconnect();
    }

    /**
     * Schedule a reconnection attempt
     * @private
     */
    _scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error(`[WebSocket] Max reconnection attempts (${this.maxReconnectAttempts}) reached`);
            this._emit('error', { 
                type: 'max_reconnect_attempts', 
                message: `Failed to reconnect after ${this.maxReconnectAttempts} attempts` 
            });
            return;
        }

        const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts);
        this.reconnectAttempts++;

        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }

    /**
     * Handle WebSocket errors
     * @param {Error} error - The error that occurred
     * @private
     */
    _handleError(error) {
        console.error('[WebSocket] Error:', error);
        this._emit('error', { 
            type: 'connection_error', 
            error: error.message || 'Unknown WebSocket error' 
        });
    }

    /**
     * Emit an event to all registered listeners
     * @param {string} event - Event name
     * @param {*} data - Event data
     * @private
     */
    _emit(event, data) {
        const listeners = this.eventListeners.get(event) || [];
        listeners.forEach(callback => {
            try {
                callback(data);
            } catch (error) {
                console.error(`[WebSocket] Error in ${event} handler:`, error);
            }
        });
    }

    /**
     * Register an event listener
     * @param {string} event - Event name ('open', 'message', 'close', 'error', 'pong')
     * @param {Function} callback - Event handler function
     */
    on(event, callback) {
        if (typeof callback !== 'function') {
            throw new Error('Callback must be a function');
        }

        if (!this.eventListeners.has(event)) {
            this.eventListeners.set(event, []);
        }

        this.eventListeners.get(event).push(callback);
        return this;
    }

    /**
     * Remove an event listener
     * @param {string} event - Event name
     * @param {Function} callback - Event handler function to remove
     */
    off(event, callback) {
        if (!this.eventListeners.has(event)) return this;

        const listeners = this.eventListeners.get(event);
        const index = listeners.indexOf(callback);
        
        if (index !== -1) {
            listeners.splice(index, 1);
        }

        return this;
    }

    /**
     * Send a message through the WebSocket
     * @param {Object|string} data - Data to send (will be stringified if not a string)
     * @returns {boolean} - Whether the message was sent successfully
     */
    send(data) {
        if (!this.isConnected || !this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.error('[WebSocket] Cannot send message, connection not open');
            return false;
        }

        try {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            this.socket.send(message);
            return true;
        } catch (error) {
            console.error('[WebSocket] Error sending message:', error);
            this._handleError(error);
            return false;
        }
    }

    /**
     * Close the WebSocket connection
     * @param {number} [code] - Close code
     * @param {string} [reason] - Close reason
     */
    close(code, reason) {
        if (this.socket) {
            this.autoReconnect = false; // Disable auto-reconnect when closing intentionally
            this._stopPingPong();
            
            if (this.socket.readyState === WebSocket.OPEN) {
                this.socket.close(code, reason);
            } else {
                this.socket.onopen = () => this.socket.close(code, reason);
            }
            
            this.isConnected = false;
        }
    }

    /**
     * Reconnect to the WebSocket server
     */
    reconnect() {
        if (this.socket) {
            this.socket.close();
        }
        this.connect();
    }

    /**
     * Get the current connection state
     * @returns {string} - Connection state ('connecting', 'open', 'closing', 'closed')
     */
    getState() {
        if (!this.socket) return 'closed';
        
        switch (this.socket.readyState) {
            case WebSocket.CONNECTING: return 'connecting';
            case WebSocket.OPEN: return 'open';
            case WebSocket.CLOSING: return 'closing';
            case WebSocket.CLOSED: return 'closed';
            default: return 'unknown';
        }
    }
}

export { WebSocketService };
