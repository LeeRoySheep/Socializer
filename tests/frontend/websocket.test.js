// @ts-nocheck
const { jest } = require('@jest/globals');

// Mock WebSocket for testing
const WebSocket = require('ws');
class MockWebSocket {
    constructor(url, protocols) {
        this.url = url;
        this.protocols = protocols;
        this.readyState = 1; // OPEN
        this.binaryType = 'arraybuffer';
        this.onopen = null;
        this.onmessage = null;
        this.onclose = null;
        this.onerror = null;
        this.sentMessages = [];
        this.isClosed = false;
        
        // Auto-connect
        setTimeout(() => {
            if (this.onopen) this.onopen({});
        }, 0);
    }
    
    send(data) {
        const parsedData = typeof data === 'string' ? JSON.parse(data) : data;
        this.sentMessages.push(parsedData);
        
        // Auto-respond to ping messages
        if (parsedData?.type === 'ping') {
            setTimeout(() => {
                if (this.onmessage) {
                    this.onmessage({
                        data: JSON.stringify({
                            type: 'pong',
                            timestamp: Date.now()
                        })
                    });
                }
            }, 0);
        }
    }
    
    close() {
        this.isClosed = true;
        if (this.onclose) this.onclose({ code: 1000, reason: 'Test closure' });
    }
    
    simulateMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) });
        }
    }
    
    simulateError() {
        if (this.onerror) {
            this.onerror(new Error('Test error'));
        }
    }
    
    close(code, reason) {
        this.isClosed = true;
        if (this.onclose) {
            this.onclose({
                code: code || 1000,
                reason: reason || 'Normal closure',
                wasClean: true
            });
        }
    }
}

// Mock global WebSocket
const originalWebSocket = global.WebSocket;
const mockUsers = [
    { id: '1', username: 'testuser1', status: 'online' },
    { id: '2', username: 'testuser2', status: 'online' }
];

describe('WebSocket Connection', () => {
    let mockSocket;
    let originalConsoleError;
    
    beforeAll(() => {
        // Mock console.error to prevent test output pollution
        originalConsoleError = console.error;
        console.error = jest.fn();
        
        // Mock WebSocket
        global.WebSocket = jest.fn((url, protocols) => {
            mockSocket = new MockWebSocket(url, protocols);
            return mockSocket;
        });
        
        // Mock DOM elements
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
            </div>
        `;
        
        // Import the chat module
        await import('../../static/js/chat.js');
    });
    
    afterAll(() => {
        // Restore original WebSocket and console.error
        global.WebSocket = originalWebSocket;
        console.error = originalConsoleError;
    });
    
    beforeEach(() => {
        // Reset mocks before each test
        jest.clearAllMocks();
        if (mockSocket) {
            mockSocket.sentMessages = [];
            mockSocket.isClosed = false;
        }
    });
    
    test('should establish WebSocket connection', (done) => {
        // Mock the token and current user
        window.ACCESS_TOKEN = 'test-token';
        window.currentUser = { id: '1', username: 'testuser1' };
        
        // Trigger connection
        initWebSocket().then(() => {
            expect(global.WebSocket).toHaveBeenCalledTimes(1);
            expect(mockSocket).toBeDefined();
            expect(mockSocket.binaryType).toBe('arraybuffer');
            
            // Verify handshake was sent
            const handshake = mockSocket.sentMessages.find(m => m.type === 'handshake');
            expect(handshake).toBeDefined();
            expect(handshake.user_id).toBe('1');
            expect(handshake.username).toBe('testuser1');
            
            // Verify online users request was sent
            const onlineUsersRequest = mockSocket.sentMessages.find(m => m.type === 'get_online_users');
            expect(onlineUsersRequest).toBeDefined();
            
            done();
        }).catch(done);
    });
    
    test('should update online users list when receiving users', (done) => {
        // Mock the token and current user
        window.ACCESS_TOKEN = 'test-token';
        window.currentUser = { id: '1', username: 'testuser1' };
        
        // Trigger connection
        initWebSocket().then(() => {
            // Simulate receiving online users
            const usersMessage = {
                type: 'online_users',
                users: mockUsers,
                timestamp: new Date().toISOString()
            };
            
            mockSocket.onmessage({ data: JSON.stringify(usersMessage) });
            
            // Check if online users list was updated
            const onlineCount = document.getElementById('online-count');
            const usersList = document.getElementById('online-users-list');
            
            expect(onlineCount.textContent).toBe('2');
            expect(usersList.children.length).toBe(2);
            expect(usersList.textContent).toContain('testuser1');
            expect(usersList.textContent).toContain('testuser2');
            
            done();
        }).catch(done);
    });
    
    test('should handle ping-pong messages', (done) => {
        // Mock the token and current user
        window.ACCESS_TOKEN = 'test-token';
        window.currentUser = { id: '1', username: 'testuser1' };
        
        // Mock Date.now() for consistent testing
        const originalNow = Date.now;
        Date.now = jest.fn(() => 1000);
        
        // Trigger connection
        initWebSocket().then(() => {
            // Fast-forward time to trigger ping
            Date.now = jest.fn(() => 11000); // 10 seconds later
            
            // The ping should be sent automatically
            jest.advanceTimersByTime(10000);
            
            // Check if ping was sent
            const pingMessage = mockSocket.sentMessages.find(m => m.type === 'ping');
            expect(pingMessage).toBeDefined();
            
            // The mock WebSocket should auto-respond with pong
            // Check if the pong was received by verifying no error was logged
            expect(console.error).not.toHaveBeenCalled();
            
            // Restore Date.now
            Date.now = originalNow;
            
            done();
        }).catch(done);
    });
    
    test('should handle disconnection and attempt to reconnect', (done) => {
        // Mock the token and current user
        window.ACCESS_TOKEN = 'test-token';
        window.currentUser = { id: '1', username: 'testuser1' };
        
        // Mock setTimeout for testing
        jest.useFakeTimers();
        
        // Trigger connection
        initWebSocket().then(() => {
            // Simulate connection close
            mockSocket.close(1006, 'Connection failed');
            
            // Fast-forward time to trigger reconnection
            jest.advanceTimersByTime(1000);
            
            // Should have created a new WebSocket
            expect(global.WebSocket).toHaveBeenCalledTimes(2);
            
            // Clean up
            jest.useRealTimers();
            done();
        }).catch(done);
    });
});
