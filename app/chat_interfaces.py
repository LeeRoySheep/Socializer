from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class ChatInterface(ABC):
    """Abstract base class for chat interfaces."""
    
    @abstractmethod
    def send_message(self, message: str, message_type: str = "chat_message", **kwargs) -> None:
        """Send a message through the interface."""
        pass
    
    @abstractmethod
    def receive_message(self) -> str:
        """Receive a message from the interface."""
        pass


class TerminalInterface(ChatInterface):
    """Chat interface for terminal-based interaction."""
    
    def send_message(self, message: str, message_type: str = "chat_message", **kwargs) -> None:
        """Print message to terminal with formatting based on message type."""
        if message_type == "system":
            print(f"\n[SYSTEM] {message}")
        elif message_type == "error":
            print(f"\n[ERROR] {message}")
        else:
            print(f"\n{message}")
    
    def receive_message(self) -> str:
        """Get input from terminal."""
        return input("You: ")


class WebSocketInterface(ChatInterface):
    """Chat interface for WebSocket-based interaction."""
    
    def __init__(self, websocket):
        self.websocket = websocket
    
    async def send_message(self, message: str, message_type: str = "chat_message", **kwargs) -> None:
        """Send message through WebSocket connection."""
        message_data = {
            "type": message_type,
            "message": message,
            **kwargs
        }
        if hasattr(self.websocket, 'send_json'):
            await self.websocket.send_json(message_data)
    
    async def receive_message(self) -> str:
        """Receive message from WebSocket connection."""
        data = await self.websocket.receive_text()
        return data
