import { LogoutButton } from '../auth/LogoutButton.js';

export class UIManager {
    constructor() {
        this.elements = {
            messagesContainer: document.getElementById('messages'),
            messageForm: document.getElementById('message-form'),
            messageInput: document.getElementById('message-input'),
            userList: document.getElementById('user-list'),
            onlineCount: document.getElementById('online-count'),
            typingIndicator: document.getElementById('typing-indicator'),
            currentRoom: document.getElementById('current-room')
        };

        this.typingUsers = new Set();
        this.typingTimeout = null;
        this.typingIndicatorDuration = 2000; // 2 seconds
        
        // Initialize logout button if it exists
        if (document.getElementById('logout-btn')) {
            const logoutButton = new LogoutButton();
            logoutButton.render();
        }
    }

    initialize({ onSendMessage }) {
        // Set up event listeners for message form
        if (this.elements.messageForm) {
            this.elements.messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                const message = this.elements.messageInput.value.trim();
                if (message) {
                    onSendMessage(message);
                    this.elements.messageInput.value = '';
                }
            });
        }

        // Typing indicator
        if (this.elements.messageInput) {
            let typingTimer;
            let isTyping = false;

            this.elements.messageInput.addEventListener('input', () => {
                if (!isTyping) {
                    isTyping = true;
                    // Notify server that user started typing
                    // This would be handled by the ChatService
                }

                // Reset the typing timer on each input
                clearTimeout(typingTimer);
                typingTimer = setTimeout(() => {
                    isTyping = false;
                    // Notify server that user stopped typing
                    // This would be handled by the ChatService
                }, 1000);
            });
        }

        // Initialize any UI components
        this.initializeComponents();
    }

    initializeComponents() {
        // Initialize any UI components here
        // For example, tooltips, modals, etc.
    }

    addMessage(message) {
        const messageElement = this.createMessageElement(message);
        this.elements.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    createMessageElement(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.sender === 'system' ? 'system' : 'received'}`;
        
        const time = new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-sender">${this.escapeHtml(message.sender)}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message.content)}</div>
        `;
        
        return messageDiv;
    }

    updateUserList(users) {
        if (!this.elements.userList) return;

        // Clear current user list
        this.elements.userList.innerHTML = '';

        // Update online count
        if (this.elements.onlineCount) {
            this.elements.onlineCount.textContent = `${users.length} online`;
        }

        // Add each user to the list
        users.forEach(user => {
            const userElement = this.createUserElement(user);
            this.elements.userList.appendChild(userElement);
        });
    }

    createUserElement(user) {
        const userElement = document.createElement('div');
        userElement.className = 'user';
        userElement.innerHTML = `
            <span class="user-status ${user.online ? 'online' : 'offline'}"></span>
            <span class="user-name">${this.escapeHtml(user.username)}</span>
        `;
        return userElement;
    }

    showTypingIndicator(user) {
        if (!user) return;

        // Add user to typing users
        this.typingUsers.add(user.username);
        this.updateTypingIndicator();

        // Clear previous timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }

        // Set timeout to remove typing indicator
        this.typingTimeout = setTimeout(() => {
            this.typingUsers.delete(user.username);
            this.updateTypingIndicator();
        }, this.typingIndicatorDuration);
    }

    updateTypingIndicator() {
        if (!this.elements.typingIndicator) return;

        if (this.typingUsers.size === 0) {
            this.elements.typingIndicator.textContent = '';
            return;
        }

        const users = Array.from(this.typingUsers);
        let text = '';

        if (users.length === 1) {
            text = `${users[0]} is typing...`;
        } else if (users.length === 2) {
            text = `${users[0]} and ${users[1]} are typing...`;
        } else {
            text = `${users[0]} and ${users.length - 1} others are typing...`;
        }

        this.elements.typingIndicator.textContent = text;
    }

    showError(message) {
        // Create error message element
        const errorElement = document.createElement('div');
        errorElement.className = 'alert alert-danger';
        errorElement.textContent = message;

        // Add to the top of the messages container
        this.elements.messagesContainer.insertBefore(
            errorElement,
            this.elements.messagesContainer.firstChild
        );

        // Remove after 5 seconds
        setTimeout(() => {
            errorElement.remove();
        }, 5000);
    }

    showSuccess(message) {
        // Similar to showError but with success styling
        const successElement = document.createElement('div');
        successElement.className = 'alert alert-success';
        successElement.textContent = message;

        this.elements.messagesContainer.insertBefore(
            successElement,
            this.elements.messagesContainer.firstChild
        );

        setTimeout(() => {
            successElement.remove();
        }, 3000);
    }

    scrollToBottom() {
        this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
    }

    escapeHtml(unsafe) {
        if (!unsafe) return '';
        return unsafe
            .toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    setLoading(loading) {
        // You can implement a loading state if needed
        document.body.style.cursor = loading ? 'wait' : '';
    }
}

export default UIManager;
