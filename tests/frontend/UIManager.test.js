import { jest } from '@jest/globals';
import { UIManager } from '../../static/js/modules/UIManager.js';

describe('UIManager', () => {
    let uiManager;
    
    // Mock DOM elements
    const mockElements = {
        onlineUsersList: document.createElement('div'),
        onlineCount: document.createElement('div'),
        chatMessages: document.createElement('div'),
        messageInput: document.createElement('input'),
        sendButton: document.createElement('button'),
        typingIndicator: document.createElement('div'),
        connectionStatus: document.createElement('div')
    };
    
    // Mock UserManager
    const mockUserManager = {
        currentUser: { id: '1', username: 'testuser' },
        getOnlineUsers: jest.fn().mockReturnValue([
            { id: '1', username: 'testuser', status: 'online' },
            { id: '2', username: 'otheruser', status: 'online' }
        ]),
        getUserColor: jest.fn().mockImplementation(id => 
            id === '1' ? '#ff0000' : '#0000ff'
        )
    };

    beforeEach(() => {
        // Reset mock elements
        document.body.innerHTML = `
            <div id="chat-container">
                <div id="online-users">
                    <div id="online-count">0</div>
                    <ul id="online-users-list"></ul>
                </div>
                <div id="chat-messages"></div>
                <div id="typing-indicator"></div>
                <input id="message-input" />
                <button id="send-button">Send</button>
                <div id="connection-status"></div>
            </div>
        `;
        
        // Create UIManager instance
        uiManager = new UIManager(mockUserManager, {
            onlineUsersList: document.getElementById('online-users-list'),
            onlineCount: document.getElementById('online-count'),
            chatMessages: document.getElementById('chat-messages'),
            messageInput: document.getElementById('message-input'),
            sendButton: document.getElementById('send-button'),
            typingIndicator: document.getElementById('typing-indicator'),
            connectionStatus: document.getElementById('connection-status')
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
    });

    test('should initialize with correct elements', () => {
        expect(uiManager.elements.onlineUsersList).toBeDefined();
        expect(uiManager.elements.chatMessages).toBeDefined();
        expect(uiManager.userManager).toBe(mockUserManager);
    });

    test('should update online users list', () => {
        // Mock getOnlineUsers to return test users
        mockUserManager.getOnlineUsers.mockReturnValue([
            { id: '1', username: 'testuser', status: 'online' },
            { id: '2', username: 'otheruser', status: 'online' }
        ]);
        
        uiManager.updateOnlineUsersList();
        
        const userItems = document.querySelectorAll('#online-users-list li');
        expect(userItems.length).toBe(2);
        expect(userItems[0].textContent).toContain('testuser');
        expect(userItems[1].textContent).toContain('otheruser');
        
        // Check if online count was updated
        expect(document.getElementById('online-count').textContent).toBe('2');
    });

    test('should add message to chat', () => {
        const message = {
            id: '123',
            user_id: '1',
            username: 'testuser',
            content: 'Hello, world!',
            timestamp: '2023-01-01T00:00:00Z'
        };
        
        uiManager.addMessage(message);
        
        const messages = document.querySelectorAll('#chat-messages .message');
        expect(messages.length).toBe(1);
        expect(messages[0].textContent).toContain('testuser');
        expect(messages[0].textContent).toContain('Hello, world!');
    });

    test('should update connection status', () => {
        uiManager.updateConnectionStatus(true, 'Connected');
        
        const statusEl = document.getElementById('connection-status');
        expect(statusEl.textContent).toBe('Connected');
        expect(statusEl.className).toContain('connected');
        
        // Test disconnection
        uiManager.updateConnectionStatus(false, 'Disconnected');
        expect(statusEl.className).toContain('disconnected');
    });

    test('should show typing indicator', () => {
        uiManager.showTypingIndicator('otheruser');
        
        const indicator = document.getElementById('typing-indicator');
        expect(indicator.textContent).toContain('otheruser is typing');
        expect(indicator.style.display).not.toBe('none');
        
        // Test hiding the indicator
        uiManager.hideTypingIndicator();
        expect(indicator.style.display).toBe('none');
    });

    test('should clear message input', () => {
        const input = document.getElementById('message-input');
        input.value = 'Test message';
        
        uiManager.clearMessageInput();
        expect(input.value).toBe('');
    });

    test('should get message input value', () => {
        const input = document.getElementById('message-input');
        input.value = 'Test message';
        
        expect(uiManager.getMessageInput()).toBe('Test message');
    });

    test('should scroll chat to bottom', () => {
        // Mock scrollIntoView
        const scrollIntoViewMock = jest.fn();
        document.getElementById('chat-messages').scrollIntoView = scrollIntoViewMock;
        
        uiManager.scrollToBottom();
        expect(scrollIntoViewMock).toHaveBeenCalledWith({ behavior: 'smooth' });
    });
});
