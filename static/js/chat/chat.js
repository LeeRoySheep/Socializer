import { authService } from '../auth/AuthService.js';
import { ChatService } from './services/ChatService.js';
import { UIManager } from './ui/UIManager.js';

class ChatApp {
    constructor() {
        // Check if user is authenticated
        const token = authService.getToken();
        if (!token) {
            window.location.href = '/login';
            return;
        }
        
        this.chatService = new ChatService();
        this.uiManager = new UIManager();
        
        this.initialize();
    }

    async initialize() {
        try {
            // Initialize UI
            this.uiManager.initialize({
                onSendMessage: (message) => this.handleSendMessage(message)
            });

            // Initialize chat service with the token
            await this.chatService.initialize({
                token: authService.getToken(),
                onMessage: (message) => this.uiManager.addMessage(message),
                onUserListUpdate: (users) => this.uiManager.updateUserList(users),
                onTyping: (user) => this.uiManager.showTypingIndicator(user)
            });

            // Load initial data
            await this.loadInitialData();

        } catch (error) {
            console.error('Failed to initialize chat:', error);
            this.uiManager.showError('Failed to initialize chat. Please try again.');
        }
    }

    async loadInitialData() {
        try {
            // Load initial messages
            const messages = await this.chatService.getMessages();
            messages.forEach(msg => this.uiManager.addMessage(msg));
            
            // Load online users
            const users = await this.chatService.getOnlineUsers();
            this.uiManager.updateUserList(users);
            
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.uiManager.showError('Failed to load chat data');
        }
    }

    async handleSendMessage(message) {
        try {
            await this.chatService.sendMessage({
                content: message,
                timestamp: new Date().toISOString(),
                sender: this.authService.getCurrentUser()
            });
        } catch (error) {
            console.error('Failed to send message:', error);
            this.uiManager.showError('Failed to send message');
        }
    }

    async handleLogout() {
        try {
            await authService.logout();
            // The logout method will handle the redirect
        } catch (error) {
            console.error('Logout failed:', error);
            this.uiManager.showError('Logout failed');
            // Still redirect to login page even if there was an error
            window.location.href = '/login';
        }
    }
}

// Start the application when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
});
