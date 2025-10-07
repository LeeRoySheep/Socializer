import { jest } from '@jest/globals';
import { ChatController } from '../../static/js/modules/ChatController.js';

// Mock dependencies
jest.unstable_mockModule('../../static/js/modules/WebSocketService.js', () => ({
    WebSocketService: jest.fn().mockImplementation(() => ({
        connect: jest.fn(),
        sendMessage: jest.fn(),
        on: jest.fn(),
        off: jest.fn(),
        disconnect: jest.fn()
    }))
}));

jest.unstable_mockModule('../../static/js/modules/UserManager.js', () => ({
    UserManager: jest.fn().mockImplementation(() => ({
        currentUser: { id: '1', username: 'testuser' },
        getOnlineUsers: jest.fn(),
        addOnlineUser: jest.fn(),
        removeOnlineUser: jest.fn(),
        updateUserStatus: jest.fn()
    }))
}));

jest.unstable_mockModule('../../static/js/modules/UIManager.js', () => ({
    UIManager: jest.fn().mockImplementation(() => ({
        init: jest.fn(),
        addMessage: jest.fn(),
        updateOnlineUsers: jest.fn(),
        on: jest.fn(),
        showError: jest.fn()
    }))
}));

// Import the mocks
const { WebSocketService } = await import('../../static/js/modules/WebSocketService.js');
const { UserManager } = await import('../../static/js/modules/UserManager.js');
const { UIManager } = await import('../../static/js/modules/UIManager.js');

describe('ChatController', () => {
    let chatController;
    let mockWebSocketService;
    let mockUserManager;
    let mockUIManager;
    
    const testConfig = {
        websocketUrl: 'ws://test-websocket',
        roomId: 'test-room',
        currentUser: {
            id: '1',
            username: 'testuser',
            token: 'test-token'
        }
    };

    beforeEach(() => {
        // Reset all mocks
        jest.clearAllMocks();
        
        // Create mock instances
        mockWebSocketService = new WebSocketService();
        mockUserManager = new UserManager(testConfig.currentUser);
        mockUIManager = new UIManager(mockUserManager, {});
        
        // Mock WebSocketService methods
        mockWebSocketService.on = jest.fn();
        mockWebSocketService.connect = jest.fn();
        mockWebSocketService.send = jest.fn();
        mockWebSocketService.disconnect = jest.fn();
        
        // Mock UserManager methods
        mockUserManager.getOnlineUsers = jest.fn().mockReturnValue([
            { id: '1', username: 'testuser', status: 'online' }
        ]);
        
        // Create chat controller with mock dependencies
        chatController = new ChatController(
            mockWebSocketService,
            mockUserManager,
            mockUIManager,
            testConfig
        );
    });

    test('should initialize with correct properties', () => {
        expect(chatController.websocketService).toBe(mockWebSocketService);
        expect(chatController.userManager).toBe(mockUserManager);
        expect(chatController.uiManager).toBe(mockUIManager);
        expect(chatController.config).toEqual(testConfig);
    });

    test('should set up event listeners on init', () => {
        // The constructor calls init() which sets up event listeners
        expect(mockWebSocketService.on).toHaveBeenCalledWith('open', expect.any(Function));
        expect(mockWebSocketService.on).toHaveBeenCalledWith('message', expect.any(Function));
        expect(mockWebSocketService.on).toHaveBeenCalledWith('close', expect.any(Function));
        expect(mockWebSocketService.on).toHaveBeenCalledWith('error', expect.any(Function));
        
        // Check if UI event handlers are set up
        expect(mockUIManager.onEvent).toBeDefined();
    });

    test('should connect to WebSocket on init', () => {
        expect(mockWebSocketService.connect).toHaveBeenCalledWith(
            `${testConfig.websocketUrl}/${testConfig.roomId}`,
            testConfig.currentUser.token
        );
    });

    test('should handle WebSocket open event', () => {
        // Get the open handler
        const openHandler = mockWebSocketService.on.mock.calls.find(
            call => call[0] === 'open'
        )[1];
        
        // Call the open handler
        openHandler();
        
        // Should send handshake message
        expect(mockWebSocketService.send).toHaveBeenCalledWith({
            type: 'handshake',
            user_id: testConfig.currentUser.id,
            username: testConfig.currentUser.username,
            room_id: testConfig.roomId
        });
        
        // Should update connection status
        expect(mockUIManager.updateConnectionStatus).toHaveBeenCalledWith(true, 'Connected');
    });

    test('should handle incoming messages', () => {
        // Get the message handler
        const messageHandler = mockWebSocketService.on.mock.calls.find(
            call => call[0] === 'message'
        )[1];
        
        // Test chat message
        messageHandler({
            type: 'chat_message',
            id: 'msg1',
            user_id: '1',
            username: 'testuser',
            content: 'Hello, world!',
            timestamp: '2023-01-01T00:00:00Z'
        });
        
        // Should add message to UI
        expect(mockUIManager.addMessage).toHaveBeenCalledWith({
            type: 'chat_message',
            id: 'msg1',
            user_id: '1',
            username: 'testuser',
            content: 'Hello, world!',
            timestamp: '2023-01-01T00:00:00Z'
        });
        
        // Test online users update
        const users = [
            { id: '1', username: 'testuser', status: 'online' },
            { id: '2', username: 'user2', status: 'online' }
        ];
        
        messageHandler({
            type: 'online_users',
            users: users,
            timestamp: '2023-01-01T00:00:00Z'
        });
        
        // Should update online users
        expect(mockUserManager.updateOnlineUsers).toHaveBeenCalledWith(users);
        expect(mockUIManager.updateOnlineUsersList).toHaveBeenCalled();
    });

    test('should handle send message', () => {
        const testMessage = 'Hello, world!';
        
        // Simulate UI event
        mockUIManager.onEvent('send_message', testMessage);
        
        // Should send message through WebSocket
        expect(mockWebSocketService.send).toHaveBeenCalledWith({
            type: 'chat_message',
            content: testMessage,
            room_id: testConfig.roomId
        });
        
        // Should clear input
        expect(mockUIManager.clearMessageInput).toHaveBeenCalled();
    });

    test('should handle disconnection', () => {
        // Get the close handler
        const closeHandler = mockWebSocketService.on.mock.calls.find(
            call => call[0] === 'close'
        )[1];
        
        // Call the close handler
        closeHandler({ code: 1000, reason: 'Normal closure' });
        
        // Should update connection status
        expect(mockUIManager.updateConnectionStatus).toHaveBeenCalledWith(
            false,
            'Disconnected: Normal closure (1000)'
        );
    });

    test('should handle errors', () => {
        // Get the error handler
        const errorHandler = mockWebSocketService.on.mock.calls.find(
            call => call[0] === 'error'
        )[1];
        
        // Call the error handler
        const testError = new Error('Test error');
        errorHandler(testError);
        
        // Should update connection status
        expect(mockUIManager.updateConnectionStatus).toHaveBeenCalledWith(
            false,
            `Error: ${testError.message}`
        );
    });

    test('should clean up on destroy', () => {
        chatController.destroy();
        
        // Should disconnect WebSocket
        expect(mockWebSocketService.disconnect).toHaveBeenCalled();
        
        // Should clear UI event handlers
        expect(mockUIManager.onEvent).toBeNull();
    });
});
