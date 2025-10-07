# AI Chat WebSocket API

This document describes the WebSocket API for the AI Chat feature in the Socializer application. The WebSocket API allows real-time communication between the client and the AI chat agent.

## Base URL

```
ws://your-domain.com/ws/ai/ai-chat/{client_id}
```

## Authentication

The WebSocket connection requires authentication using a JWT token. The token can be provided in one of two ways:

1. **URL Query Parameter**:
   ```
   ws://your-domain.com/ws/ai/ai-chat/{client_id}?token=your_jwt_token
   ```

2. **Cookie**:
   The access token can be set as an `access_token` cookie when the WebSocket connection is established.

## Connection Flow

1. **Client** establishes a WebSocket connection to the server.
2. **Server** authenticates the client using the provided token.
3. **Server** sends a welcome message upon successful connection.
4. **Client** and **Server** can now exchange messages in real-time.

## Message Format

### Client to Server

```json
{
  "content": "Hello, AI!"
}
```

### Server to Client

1. **Welcome Message** (sent upon connection):
   ```json
   {
     "type": "system",
     "message": "Welcome to AI Chat, username! How can I assist you today?",
     "timestamp": "2025-10-01T20:00:00.000000"
   }
   ```

2. **AI Response**:
   ```json
   {
     "type": "ai_response",
     "message": "Hello! How can I help you today?",
     "timestamp": "2025-10-01T20:00:01.000000"
   }
   ```

3. **Error Message**:
   ```json
   {
     "type": "error",
     "message": "An error occurred while processing your message.",
     "timestamp": "2025-10-01T20:00:02.000000"
   }
   ```

## Example Usage

### JavaScript Example

```javascript
const connectToAIChat = async (token, clientId = `client-${Math.random().toString(36).substr(2, 9)}`) => {
  const wsUrl = `ws://localhost:8000/ws/ai/ai-chat/${clientId}?token=${token}`;
  
  const socket = new WebSocket(wsUrl);
  
  socket.onopen = () => {
    console.log('Connected to AI Chat WebSocket');
  };
  
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
    
    // Handle different message types
    switch(data.type) {
      case 'system':
        console.log('System:', data.message);
        break;
      case 'ai_response':
        console.log('AI:', data.message);
        break;
      case 'error':
        console.error('Error:', data.message);
        break;
      default:
        console.log('Unknown message type:', data);
    }
  };
  
  socket.onclose = (event) => {
    console.log('Disconnected from AI Chat WebSocket:', event.reason || 'No reason provided');
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  // Function to send a message
  const sendMessage = (content) => {
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ content }));
      return true;
    }
    return false;
  };
  
  return {
    socket,
    sendMessage,
    close: () => socket.close()
  };
};

// Example usage:
// const chat = await connectToAIChat('your_jwt_token');
// chat.sendMessage('Hello, AI!');
```

## Error Handling

- **Authentication Failure**: If the token is invalid or missing, the server will close the connection with status code 1008 (Policy Violation).
- **Invalid Message Format**: If a message is not a valid JSON object or is missing required fields, the server will respond with an error message.
- **Server Errors**: If an unexpected error occurs, the server will send an error message and may close the connection.

## Rate Limiting

To prevent abuse, the AI chat is subject to rate limiting. If a client sends too many messages in a short period, the server may close the connection.

## Testing

You can test the WebSocket API using the provided test script:

```bash
python test_ai_chat_websocket.py
```

This script will:
1. Authenticate with the server
2. Establish a WebSocket connection
3. Send test messages to the AI chat agent
4. Display responses in the console
