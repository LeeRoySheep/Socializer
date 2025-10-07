// Mock implementation of the Chat class
export class Chat {
  constructor() {
    this.socket = {
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      send: jest.fn(),
      close: jest.fn()
    };
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.messageQueue = [];
    this.setupEventListeners = jest.fn();
    this.connect = jest.fn().mockImplementation(() => {
      this.isConnected = true;
      if (this.socket.onopen) {
        this.socket.onopen();
      }
    });
    this.sendMessage = jest.fn().mockImplementation((message) => {
      if (this.isConnected && this.socket.readyState === 1) {
        this.socket.send(JSON.stringify({
          type: 'chat',
          message,
          timestamp: new Date().toISOString()
        }));
        return true;
      }
      return false;
    });
    this.addMessageToUI = jest.fn();
    this.updateConnectionStatus = jest.fn();
    this.handleError = jest.fn();
    this.handleDisconnect = jest.fn();
  }
}
