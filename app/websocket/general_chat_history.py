"""
General Chat History Manager

Maintains the last 10 messages from the general chat room
that are visible to all users when they join.

Now with database persistence to survive server restarts.

Author: Socializer Development Team
Date: 2024-11-12
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque
import json


class GeneralChatHistory:
    """
    Singleton class to maintain the last 10 messages of general chat.
    These messages are shared across all users.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeneralChatHistory, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the history buffer."""
        if not self._initialized:
            # Use deque for efficient FIFO with max size
            self._history = deque(maxlen=10)  # Automatically keeps only last 10
            self._data_manager = None  # Will be set by set_data_manager
            self._initialized = True
    
    def set_data_manager(self, data_manager) -> None:
        """
        Set the DataManager instance for database persistence.
        
        Args:
            data_manager: DataManager instance
        """
        self._data_manager = data_manager
    
    def add_message(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the history and persist to database.
        
        Args:
            message: Message dictionary containing:
                - username: Sender's username
                - content: Message content
                - timestamp: When sent
                - user_id: Sender's ID
        """
        # Ensure required fields
        if 'timestamp' not in message:
            message['timestamp'] = datetime.utcnow().isoformat()
        
        # Add to history (oldest will be automatically removed if > 10)
        self._history.append(message)
        
        # Persist to database for restart recovery
        if self._data_manager:
            try:
                # Save to database
                self._data_manager.save_general_chat_message(
                    sender_id=int(message['user_id']),
                    content=message['content']
                )
            except Exception as e:
                print(f"[WARNING] Failed to persist general chat message to database: {e}")
                # Continue anyway - in-memory history still works
    
    def get_history(self, include_system: bool = False) -> List[Dict[str, Any]]:
        """
        Get the current message history.
        
        Args:
            include_system: Whether to include system/AI messages (default: False)
        
        Returns:
            List of the last 10 messages in chronological order
        """
        if include_system:
            return list(self._history)
        
        # Filter out system and AI messages
        return [
            msg for msg in self._history 
            if msg.get('user_id') not in ['system', 'ai', 'assistant'] 
            and not msg.get('username', '').lower() in ['system', 'assistant', 'ai']
        ]
    
    def clear(self) -> None:
        """Clear the history (useful for testing or admin functions)."""
        self._history.clear()
    
    def get_history_json(self) -> str:
        """
        Get history as JSON string.
        
        Returns:
            JSON string of message history
        """
        return json.dumps(self.get_history())
    
    def load_from_database(self, messages: List[Any] = None) -> None:
        """
        Load initial history from database messages.
        
        Args:
            messages: Optional list of message objects. If None, will load from database using data_manager
        """
        self.clear()
        
        # If no messages provided, load from database
        if messages is None and self._data_manager:
            try:
                messages = self._data_manager.get_general_chat_history(limit=10)
                print(f"[INFO] Loaded {len(messages)} messages from database for general chat history")
            except Exception as e:
                print(f"[WARNING] Failed to load general chat history from database: {e}")
                return
        
        if not messages:
            return
        
        for msg in messages[-10:]:  # Take only last 10
            # Convert database message to our format
            message_dict = {
                'content': getattr(msg, 'content', ''),
                'timestamp': getattr(msg, 'created_at', datetime.utcnow()).isoformat() if hasattr(msg, 'created_at') else datetime.utcnow().isoformat(),
                'user_id': str(getattr(msg, 'sender_id', '')),
                'username': getattr(msg, 'username', 'Unknown'),
                'type': 'history'  # Mark as historical message
            }
            
            # Try to get username if not present
            if not message_dict['username'] or message_dict['username'] == 'Unknown':
                if hasattr(msg, 'sender') and hasattr(msg.sender, 'username'):
                    message_dict['username'] = msg.sender.username
            
            self._history.append(message_dict)
    
    def __len__(self) -> int:
        """Get current number of messages in history."""
        return len(self._history)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<GeneralChatHistory: {len(self)} messages>"


# Global instance
_general_chat_history = None

def get_general_chat_history() -> GeneralChatHistory:
    """
    Get the singleton instance of GeneralChatHistory.
    
    Returns:
        GeneralChatHistory instance
    """
    global _general_chat_history
    if _general_chat_history is None:
        _general_chat_history = GeneralChatHistory()
    return _general_chat_history
