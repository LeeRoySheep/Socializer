/**
 * UIManager - Handles all DOM updates and user interface interactions
 */
class UIManager {
    /**
     * Create a new UIManager
     * @param {Object} userManager - Instance of UserManager
     * @param {Object} elements - Object containing DOM elements
     */
    constructor(userManager, elements) {
        this.userManager = userManager;
        this.elements = {
            onlineUsersList: elements.onlineUsersList,
            onlineCount: elements.onlineCount,
            chatMessages: elements.chatMessages,
            messageInput: elements.messageInput,
            sendButton: elements.sendButton,
            typingIndicator: elements.typingIndicator,
            connectionStatus: elements.connectionStatus
        };
        
        // Initialize UI
        this._initUI();
    }

    /**
     * Initialize the UI
     * @private
     */
    _initUI() {
        // Set initial connection status
        this.updateConnectionStatus(false, 'Connecting...');
        
        // Hide typing indicator by default
        this.hideTypingIndicator();
        
        // Set up message input auto-resize
        this._setupMessageInput();
        
        // Initialize online users list
        this._initOnlineUsersList();
    }
    
    /**
     * Initialize the online users list
     * @private
     */
    _initOnlineUsersList() {
        if (!this.elements.onlineUsersList) return;
        
        // Clear existing content
        this.elements.onlineUsersList.innerHTML = '';
        
        // Add a title
        const title = document.createElement('div');
        title.className = 'online-users-title';
        title.textContent = 'Online Users';
        this.elements.onlineUsersList.appendChild(title);
        
        // Create container for user list
        this.onlineUsersContainer = document.createElement('div');
        this.onlineUsersContainer.className = 'online-users-container';
        this.elements.onlineUsersList.appendChild(this.onlineUsersContainer);
        
        // Add online count if element exists
        if (this.elements.onlineCount) {
            this.updateOnlineCount(0);
        }
    }

    /**
     * Set up message input with auto-resize
     * @private
     */
    _setupMessageInput() {
        const input = this.elements.messageInput;
        
        input.addEventListener('input', () => {
            // Auto-resize the textarea
            input.style.height = 'auto';
            input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
        });
        
        // Handle Enter key (send message on Shift+Enter)
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.emit('send_message', input.value.trim());
            }
        });
        
        // Handle send button click
        this.elements.sendButton.addEventListener('click', () => {
            this.emit('send_message', input.value.trim());
        });
    }

    /**
     * Update the online users list
     */
    updateOnlineUsersList() {
        const users = this.userManager.getOnlineUsers();
        const currentUserId = this.userManager.currentUser?.id;
        
        // Update online count
        this.elements.onlineCount.textContent = users.length;
        
        // Clear existing list
        this.elements.onlineUsersList.innerHTML = '';
        
        // Add each user to the list
        users.forEach(user => {
            const userEl = document.createElement('li');
            userEl.className = `user ${user.status} ${user.id === currentUserId ? 'current-user' : ''}`;
            userEl.dataset.userId = user.id;
            
            // User avatar/icon
            const avatar = document.createElement('span');
            avatar.className = 'user-avatar';
            avatar.style.backgroundColor = this.userManager.getUserColor(user.id);
            avatar.textContent = user.username.charAt(0).toUpperCase();
            
            // Username
            const username = document.createElement('span');
            username.className = 'username';
            username.textContent = user.username;
            
            // Status indicator
            const status = document.createElement('span');
            status.className = `status-indicator ${user.status}`;
            status.title = user.status === 'online' ? 'Online' : 'Offline';
            
            userEl.appendChild(avatar);
            userEl.appendChild(username);
            userEl.appendChild(status);
            
            this.elements.onlineUsersList.appendChild(userEl);
        });
    }

    /**
     * Add a message to the chat
     * @param {Object} message - Message object
     */
    addMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.user_id === this.userManager.currentUser?.id ? 'own-message' : 'other-message'}`;
        messageEl.dataset.messageId = message.id;
        
        // Message header (username and timestamp)
        const header = document.createElement('div');
        header.className = 'message-header';
        
        const username = document.createElement('span');
        username.className = 'message-username';
        username.textContent = message.username || 'Unknown';
        username.style.color = this.userManager.getUserColor(message.user_id);
        
        const timestamp = document.createElement('span');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = this._formatTimestamp(message.timestamp);
        
        header.appendChild(username);
        header.appendChild(timestamp);
        
        // Message content
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = message.content;
        
        messageEl.appendChild(header);
        messageEl.appendChild(content);
        
        this.elements.chatMessages.appendChild(messageEl);
        this.scrollToBottom();
    }

    /**
     * Update connection status
     * @param {boolean} isConnected - Whether the connection is active
     * @param {string} message - Status message
     */
    updateConnectionStatus(isConnected, message) {
        const statusEl = this.elements.connectionStatus;
        statusEl.textContent = message;
        statusEl.className = `connection-status ${isConnected ? 'connected' : 'disconnected'}`;
    }

    /**
     * Show typing indicator for a user
     * @param {string} username - Username of the typing user
     */
    showTypingIndicator(username) {
        this.elements.typingIndicator.textContent = `${username} is typing...`;
        this.elements.typingIndicator.style.display = 'block';
    }

    /**
     * Hide typing indicator
     */
    hideTypingIndicator() {
        this.elements.typingIndicator.style.display = 'none';
    }

    /**
     * Clear the message input
     */
    clearMessageInput() {
        this.elements.messageInput.value = '';
        // Reset textarea height
        this.elements.messageInput.style.height = 'auto';
    }

    /**
     * Get the current message input value
     * @returns {string} The message input value
     */
    getMessageInput() {
        return this.elements.messageInput.value;
    }

    /**
     * Scroll the chat to the bottom
     */
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    /**
     * Format a timestamp into a readable string
     * @param {string} timestamp - ISO timestamp
     * @returns {string} Formatted time
     * @private
     */
    _formatTimestamp(timestamp) {
        if (!timestamp) return '';
        
        const date = new Date(timestamp);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Emit an event
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    emit(event, data) {
        // This will be implemented by the ChatController
        if (this.onEvent) {
            this.onEvent(event, data);
        }
    }
    
    /**
     * Update the online users list
     * @param {Array} users - Array of user objects
     */
    updateOnlineUsers(users) {
        if (!this.onlineUsersContainer) return;
        
        // Clear existing users
        this.onlineUsersContainer.innerHTML = '';
        
        // Add each user to the list
        users.forEach(user => {
            if (!user || !user.user_id) return;
            
            const userElement = document.createElement('div');
            userElement.className = 'online-user';
            userElement.dataset.userId = user.user_id;
            
            // Create user status indicator
            const statusIndicator = document.createElement('span');
            statusIndicator.className = `user-status ${user.status || 'offline'}`;
            
            // Create user name element
            const userName = document.createElement('span');
            userName.className = 'user-name';
            userName.textContent = user.username || 'Unknown User';
            
            userElement.appendChild(statusIndicator);
            userElement.appendChild(userName);
            this.onlineUsersContainer.appendChild(userElement);
        });
        
        // Update online count if element exists
        if (this.elements.onlineCount) {
            this.updateOnlineCount(users.length);
        }
    }
    
    /**
     * Update the online users count
     * @param {number} count - Number of online users
     */
    updateOnlineCount(count) {
        if (!this.elements.onlineCount) return;
        this.elements.onlineCount.textContent = `${count} Online`;
    }
    
    /**
     * Add a system message to the chat
     * @param {string} message - The system message to display
     * @param {string} [type='info'] - Type of system message (info, success, error, warning)
     */
    addSystemMessage(message, type = 'info') {
        if (!this.elements.chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `message system-message system-${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        messageContent.textContent = message;
        
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = this._formatTimestamp(new Date());
        
        messageElement.appendChild(messageContent);
        messageElement.appendChild(timestamp);
        
        this.elements.chatMessages.appendChild(messageElement);
        this._scrollToBottom();
    }
    
    /**
     * Format a date as a readable timestamp
     * @param {Date} date - The date to format
     * @returns {string} Formatted time string
     * @private
     */
    _formatTimestamp(date) {
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    /**
     * Scroll the chat messages to the bottom
     * @private
     */
    _scrollToBottom() {
        if (this.elements.chatMessages) {
            this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
        }
    }
    
    /**
     * Add a system message to the chat
     * @param {string} message - The message to display
     * @param {string} type - The type of system message (info, success, warning, error)
     */
    addSystemMessage(message, type = 'info') {
        if (!this.elements.chatMessages) return;
        
        const messageElement = document.createElement('div');
        messageElement.className = `system-message system-${type}`;
        messageElement.textContent = message;
        
        this.elements.chatMessages.appendChild(messageElement);
        this._scrollToBottom();
    }
    
    /**
     * Update the online users count
     * @param {number} count - The number of online users
     */
    updateOnlineCount(count) {
        if (this.elements.onlineCount) {
            this.elements.onlineCount.textContent = count;
        }
    }
}

export { UIManager };
export default UIManager;
