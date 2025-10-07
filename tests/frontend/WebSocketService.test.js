// @ts-nocheck
const { test, expect, beforeEach, afterEach, jest: jestMock } = require('@jest/globals');

// Import the WebSocketService using require to avoid ES module issues
const { WebSocketService } = require('../../static/js/modules/WebSocketService');

// Mock the WebSocket class
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 1; // OPEN
    this.onopen = null;
    this.onmessage = null;
    this.onclose = null;
    this.onerror = null;
    this.sentMessages = [];
    
    // Auto-connect after a small delay
    setTimeout(() => {
      if (this.onopen) this.onopen({});
    }, 10);
  }
  
  send(data) {
    this.sentMessages.push(JSON.parse(data));
    return true;
  }
  
  close() {
    this.readyState = 3; // CLOSED
    if (this.onclose) this.onclose({ code: 1000, reason: 'Test closure' });
  }
}

// Store original globals
const originalWebSocket = global.WebSocket;
const originalConsole = { ...console };

beforeEach(() => {
  // Mock console
  global.console = {
    ...originalConsole,
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn(),
  };
  
  // Mock WebSocket
  global.WebSocket = MockWebSocket;
  
  // Mock timers
  jest.useFakeTimers();
});

afterEach(() => {
  // Restore originals
  global.console = originalConsole;
  global.WebSocket = originalWebSocket;
  
  // Clear all mocks and timers
  jest.clearAllMocks();
  jest.clearAllTimers();
  jest.useRealTimers();
});

describe('WebSocketService', () => {
  let webSocketService;
  const mockUrl = 'ws://test-websocket';
  
  const createWebSocketService = (options = {}) => {
    return new WebSocketService(mockUrl, {
      maxReconnectAttempts: 3,
      reconnectInterval: 100,
      pingInterval: 1000,
      pongTimeout: 500,
      ...options
    });
  };
  
  test('should initialize with default values', () => {
    const service = createWebSocketService();
    expect(service.url).toBe(mockUrl);
    expect(service.maxReconnectAttempts).toBe(3);
    expect(service.reconnectInterval).toBe(100);
    expect(service.pingInterval).toBe(1000);
    expect(service.pongTimeout).toBe(500);
  });
  
  test('should connect to WebSocket server', () => {
    const service = createWebSocketService();
    service.connect();
    
    // WebSocket should be created with the correct URL
    expect(global.WebSocket).toHaveBeenCalledWith(mockUrl);
    expect(service.socket).toBeInstanceOf(MockWebSocket);
    
    // Simulate connection open
    service.socket.onopen();
    expect(service.isConnected).toBe(true);
  });
  
  test('should handle incoming messages', () => {
    const service = createWebSocketService();
    const mockHandler = jest.fn();
    
    service.on('message', mockHandler);
    service.connect();
    
    // Simulate incoming message
    const testMessage = { type: 'test', data: 'Hello' };
    service.socket.onmessage({ data: JSON.stringify(testMessage) });
    
    // Handler should be called with parsed message
    expect(mockHandler).toHaveBeenCalledWith(testMessage);
  });
  
  test('should send messages when connected', () => {
    const service = createWebSocketService();
    service.connect();
    service.socket.onopen(); // Ensure connected
    
    const testMessage = { type: 'test', data: 'Hello' };
    service.sendMessage(testMessage);
    
    // Message should be sent as JSON string
    expect(service.socket.sentMessages).toContainEqual(testMessage);
  });
  
  test('should handle disconnection', () => {
    const service = createWebSocketService();
    const disconnectHandler = jest.fn();
    
    service.on('disconnect', disconnectHandler);
    service.connect();
    service.socket.onopen(); // Ensure connected
    
    // Simulate disconnection
    service.disconnect();
    
    // Should close the socket and update state
    expect(service.socket.readyState).toBe(3); // CLOSED
    expect(service.isConnected).toBe(false);
    expect(disconnectHandler).toHaveBeenCalled();
  });
  
  test('should attempt reconnection on connection loss', () => {
    const service = createWebSocketService({
      reconnectInterval: 100,
      maxReconnectAttempts: 2
    });
    
    service.connect();
    const originalSocket = service.socket;
    
    // Simulate connection loss
    originalSocket.onclose({ code: 1006, reason: 'Connection lost' });
    
    // Fast-forward time to trigger reconnection
    jest.advanceTimersByTime(150);
    
    // Should create a new socket for reconnection
    expect(service.socket).not.toBe(originalSocket);
    expect(global.console.log).toHaveBeenCalledWith('[WebSocket] Attempting to reconnect... (1/2)');
  });
  
  test('should handle ping-pong mechanism', () => {
    const service = createWebSocketService({
      pingInterval: 1000,
      pongTimeout: 500
    });
    
    service.connect();
    service.socket.onopen();
    
    // Fast-forward time to trigger ping
    jest.advanceTimersByTime(1100);
    
    // Should have sent a ping
    const sentMessages = service.socket.sentMessages;
    expect(sentMessages.some(msg => msg.type === 'ping')).toBe(true);
    
    // Simulate pong response
    const pingMessage = sentMessages.find(msg => msg.type === 'ping');
    service.socket.onmessage({ 
      data: JSON.stringify({ type: 'pong', timestamp: pingMessage.timestamp })
    });
    
    // Should not have triggered a pong timeout
    jest.advanceTimersByTime(600);
    expect(global.console.warn).not.toHaveBeenCalledWith('[WebSocket] Pong timeout, server not responding');
  });
  
  test('should handle pong timeout', () => {
    const service = createWebSocketService({
      pingInterval: 1000,
      pongTimeout: 500
    });
    
    service.connect();
    service.socket.onopen();
    
    // Trigger ping
    jest.advanceTimersByTime(1100);
    
    // Don't respond to ping, let it time out
    jest.advanceTimersByTime(600);
    
    // Should log a warning about pong timeout
    expect(global.console.warn).toHaveBeenCalledWith('[WebSocket] Pong timeout, server not responding');
  });
});
