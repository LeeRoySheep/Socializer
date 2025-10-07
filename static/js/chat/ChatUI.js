import { chatService } from './ChatService.js';
import { authService } from '../auth/AuthService.js';

export class ChatUI {
    constructor(containerId = 'chat-container') {
        this.container = document.getElementById(containerId);
        this.messagesContainer = null;
        this.messageInput = null;
        this.sendButton = null;
        this.unsubscribe = null;
        this.containerId = containerId;
        
        if (!this.container) {
            console.error(`Chat container with ID '${containerId}' not found`);
            return;
        }
        
        this.initialize();
    }
    
    initialize() {
        // Create chat UI elements
        this.container.innerHTML = `
            <div class="chat-window">
                <div class="chat-messages" id="chat-messages"></div>
                <div class="chat-input-container">
                    <input type="text" id="message-input" placeholder="Type your message...">
                    <button id="send-button">Send</button>
                </div>
            </div>
            <style>
                .chat-window {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                    max-width: 800px;
                    margin: 0 auto;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    overflow: hidden;
                }
                
                .chat-messages {
                    flex: 1;
                    padding: 16px;
                    overflow-y: auto;
                    background-color: #f9f9f9;
                }
                
                .message {
                    margin-bottom: 12px;
                    padding: 8px 12px;
                    border-radius: 8px;
                    max-width: 70%;
                    word-wrap: break-word;
                }
                
                .message.user {
                    background-color: #007bff;
                    color: white;
                    margin-left: auto;
                    border-bottom-right-radius: 2px;
                }
                
                .message.system {
                    background-color: #e9ecef;
                    margin-right: auto;
                    border-bottom-left-radius: 2px;
                }
                
                .message .sender {
                    font-weight: bold;
                    font-size: 0.9em;
                    margin-bottom: 4px;
                }
                
                .message .timestamp {
                    font-size: 0.7em;
                    opacity: 0.8;
                    margin-top: 4px;
                    display: block;
                    text-align: right;
                }
                
                .chat-input-container {
                    display: flex;
                    padding: 12px;
                    background-color: #fff;
                    border-top: 1px solid #eee;
                }
                
                #message-input {
                    flex: 1;
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 20px;
                    margin-right: 8px;
                    outline: none;
                }
                
                #send-button {
                    padding: 8px 20px;
                    background-color: #007bff;
                    color: white;
                    border: none;
                    border-radius: 20px;
                    cursor: pointer;
                }
                
                #send-button:hover {
                    background-color: #0056b3;
                }
                
                #send-button:disabled {
                    background-color: #ccc;
                    cursor: not-allowed;
                }
            </style>
        `;
        
        // Get references to elements
        this.messagesContainer = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Connect to WebSocket
        this.connectToChat();
    }
    
    setupEventListeners() {
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Handle window unload
        window.addEventListener('beforeunload', () => {
            if (this.unsubscribe) {
                this.unsubscribe();
            }
            chatService.disconnect();
        });
    }
    
    async connectToChat() {
        try {
            const token = authService.getToken();
            if (!token) {
                this.addSystemMessage('Please log in to use the chat');
                return;
            }
            
            // Connect to WebSocket
            await chatService.connect(token);
            
            // Subscribe to incoming messages
            this.unsubscribe = chatService.onMessage((message) => {
                this.handleIncomingMessage(message);
            });
            
            this.addSystemMessage('Connected to chat');
            
        } catch (error) {
            console.error('Failed to connect to chat:', error);
            this.addSystemMessage('Failed to connect to chat. Please refresh the page to try again.');
        }
    }
    
    async sendMessage() {
        const messageText = this.messageInput.value.trim();
        if (!messageText) return;
        
        // Add message to UI immediately for better UX
        this.addMessage({
            type: 'chat_message',
            message: messageText,
            sender: 'You',
            timestamp: new Date().toISOString()
        }, 'user');
        
        // Clear input
        this.messageInput.value = '';
        
        try {
            // Send message via WebSocket
            await chatService.sendMessage(messageText);
        } catch (error) {
            console.error('Failed to send message:', error);
            this.addSystemMessage('Failed to send message. Please try again.');
        }
    }
    
    handleIncomingMessage(message) {
        console.log('Handling message:', message);
        
        switch (message.type) {
            case 'chat_message':
                this.addMessage({
                    ...message,
                    sender: message.sender || 'Unknown User'
                }, message.sender === 'You' ? 'user' : 'system');
                break;
                
            case 'system_message':
                this.addSystemMessage(message.message);
                break;
                
            case 'user_joined':
                this.addSystemMessage(`${message.username} joined the chat`);
                break;
                
            case 'user_left':
                this.addSystemMessage(`${message.username} left the chat`);
                break;
                
            default:
                console.log('Unhandled message type:', message.type);
        }
    }
    
    addMessage(message, type = 'system') {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${type}`;
        
        const timestamp = new Date(message.timestamp).toLocaleTimeString();
        
        messageElement.innerHTML = `
            <div class="sender">${message.sender}</div>
            <div class="content">${this.escapeHtml(message.message)}</div>
            <div class="timestamp">${timestamp}</div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    addSystemMessage(text) {
        this.addMessage({
            type: 'system_message',
            message: text,
            sender: 'System',
            timestamp: new Date().toISOString()
        }, 'system');
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}

// Auto-initialize if this script is included directly
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ChatUI());
} else {
    new ChatUI();
}
