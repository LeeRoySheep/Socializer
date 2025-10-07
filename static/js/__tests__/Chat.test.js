/**
 * Integration tests for WebSocket chat functionality
 * These tests require the server to be running on localhost:8000
 * @jest-environment node
 */

// Import dependencies
import WebSocket from 'ws';
import fetch from 'node-fetch';

// Enable fetch globally for node-fetch
global.fetch = fetch;

// Configuration
const WS_URL = 'ws://localhost:8000/ws/chat';
const TEST_USER = {
    username: 'testuser',
    password: 'testpass123',
    email: 'test@example.com'
};

// Helper function to get auth token
async function getAuthToken() {
    try {
        const response = await fetch('http://localhost:8000/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: TEST_USER.username,
                password: TEST_USER.password
            })
        });
        
        if (!response.ok) {
            throw new Error(`Login failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        return data.access_token;
    } catch (error) {
        console.error('Error getting auth token:', error);
        throw error;
    }
}

// Helper function to create a WebSocket connection
function createWebSocketConnection(token) {
    return new Promise((resolve, reject) => {
        try {
            const ws = new WebSocket(`${WS_URL}?token=${encodeURIComponent(token)}`);
            
            ws.on('open', () => {
                console.log('WebSocket connection established');
                resolve(ws);
            });
            
            ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                reject(error);
            });
            
            // Set a timeout for connection
            setTimeout(() => {
                reject(new Error('WebSocket connection timeout'));
            }, 5000);
            
        } catch (error) {
            reject(error);
        }
    });
}

// Increase the test timeout since we're making real network requests
jest.setTimeout(30000);

describe('Real WebSocket Server Integration', () => {
    let wsClient;
    let authToken;
    let receivedMessages = [];

    // Setup before all tests
    beforeAll(async () => {
        try {
            // Get authentication token
            authToken = await getAuthToken();
            console.log('Obtained auth token:', authToken ? 'Success' : 'Failed');
            
            // Create WebSocket connection
            wsClient = await createWebSocketConnection(authToken);
            
            // Set up message handler
            wsClient.on('message', (data) => {
                try {
                    const message = JSON.parse(data);
                    receivedMessages.push(message);
                    console.log('Received message:', message);
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            });
            
            // Wait a bit for the connection to be fully established
            await new Promise(resolve => setTimeout(resolve, 1000));
            
        } catch (error) {
            console.error('Test setup failed:', error);
            throw error;
        }
    });
    
    // Cleanup after all tests
    afterAll(() => {
        if (wsClient) {
            wsClient.close();
        }
    });
    
    // Reset received messages before each test
    beforeEach(() => {
        receivedMessages = [];
    });
    
    test('should successfully connect to WebSocket server', () => {
        expect(wsClient).toBeDefined();
        expect(wsClient.readyState).toBe(WebSocket.OPEN);
    });
    
    test('should be able to send and receive messages', async () => {
        const testMessage = {
            type: 'chat',
            message: 'Hello from test!',
            timestamp: new Date().toISOString()
        };
        
        // Send message
        wsClient.send(JSON.stringify(testMessage));
        
        // Wait for the message to be processed
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Check if we received any messages
        expect(receivedMessages.length).toBeGreaterThan(0);
        
        // Check if our message was acknowledged
        const ackMessage = receivedMessages.find(
            msg => msg.type === 'ack' && msg.originalMessage === testMessage.message
        );
        
        expect(ackMessage).toBeDefined();
    });
    
    test('should receive system messages', async () => {
        // Wait for system messages (like user join notifications)
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Check if we received any system messages
        const systemMessages = receivedMessages.filter(
            msg => msg.type === 'system'
        );
        
        expect(systemMessages.length).toBeGreaterThan(0);
    });
    
    test('should handle multiple messages in sequence', async () => {
        const messages = [
            { type: 'chat', message: 'First message', timestamp: new Date().toISOString() },
            { type: 'chat', message: 'Second message', timestamp: new Date().toISOString() },
            { type: 'chat', message: 'Third message', timestamp: new Date().toISOString() }
        ];
        
        // Send all messages
        for (const msg of messages) {
            wsClient.send(JSON.stringify(msg));
            await new Promise(resolve => setTimeout(resolve, 200)); // Small delay between messages
        }
        
        // Wait for all messages to be processed
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Check if we received acknowledgments for all messages
        const ackMessages = receivedMessages.filter(
            msg => msg.type === 'ack' && messages.some(m => m.message === msg.originalMessage)
        );
        
        expect(ackMessages.length).toBe(messages.length);
    });
    
    test('should handle connection errors gracefully', async () => {
        // Force close the connection
        wsClient.close();
        
        // Try to send a message on closed connection
        const sendMessage = () => {
            wsClient.send(JSON.stringify({
                type: 'chat',
                message: 'This should fail',
                timestamp: new Date().toISOString()
            }));
        };
        
        // Should throw an error or trigger an error event
        expect(sendMessage).toThrow();
    });
});
