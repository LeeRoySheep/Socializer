"""
User-specific AI agent with isolated memory access.

Each user gets their own AI agent instance that can only access
that user's encrypted conversation memory.

Author: Socializer Development Team
Date: 2024-11-12
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from memory.secure_memory_manager import SecureMemoryManager


class UserAgent:
    """
    User-specific AI agent with isolated memory access.
    
    This class ensures that each user has their own AI agent that:
    1. Can only access that specific user's conversation memory
    2. Uses user-specific encryption for all stored data
    3. Maintains conversation context across sessions
    
    Attributes:
        user: User object
        _llm: Language model instance
        _data_manager: DataManager for persistence
        _memory_manager: SecureMemoryManager for this user
        _conversation_buffer: Temporary buffer for current conversation
    """
    
    def __init__(self, user, llm, data_manager):
        """
        Initialize a user-specific AI agent.
        
        Args:
            user: User object with id and encryption_key
            llm: Language model instance
            data_manager: DataManager for database operations
        """
        self.user = user
        self._llm = llm
        self._data_manager = data_manager
        self._memory_manager = SecureMemoryManager(data_manager, user)
        self._conversation_buffer = []
        
        # Load existing memory on initialization
        self._load_context()
    
    def _load_context(self) -> None:
        """Load existing conversation context from encrypted memory."""
        memory = self._memory_manager.recall_conversation_memory()
        if memory and "messages" in memory:
            # Load recent messages into buffer for context
            recent_messages = memory.get("messages", [])[-10:]  # Last 10 messages
            self._conversation_buffer = recent_messages.copy()
    
    def add_to_memory(self, message: Dict[str, Any]) -> None:
        """
        Add a message to the agent's memory.
        
        Args:
            message: Message dictionary with role/content or type/content
        """
        # Add timestamp if not present
        if "timestamp" not in message:
            message["timestamp"] = datetime.now().isoformat()
        
        # Add user association
        message["user_id"] = self.user.id
        
        # Determine message type
        message_type = message.get("type", "ai")
        
        # Add to buffer
        self._conversation_buffer.append(message)
        
        # Add to memory manager
        self._memory_manager.add_message(message, message_type)
        
        # Auto-save every 5 messages
        if len(self._conversation_buffer) % 5 == 0:
            self.save_memory()
    
    def recall_memory(self) -> Optional[Dict[str, Any]]:
        """
        Recall the user's conversation memory.
        
        Returns:
            Dict containing conversation memory or None
        """
        return self._memory_manager.recall_conversation_memory()
    
    def save_memory(self) -> bool:
        """
        Save the current conversation buffer to encrypted storage.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Get all messages from memory manager
        current_memory = self._memory_manager.get_current_memory()
        all_messages = current_memory.get("messages", [])
        
        # Add buffer messages that aren't already in memory
        for msg in self._conversation_buffer:
            # Check for duplicates using content and timestamp
            is_duplicate = any(
                existing.get('content') == msg.get('content') and 
                existing.get('timestamp') == msg.get('timestamp')
                for existing in all_messages
            )
            if not is_duplicate:
                all_messages.append(msg)
        
        # Determine message types and save
        success = self._memory_manager.save_combined_memory(
            all_messages,
            max_general=10,  # Keep last 10 general chat messages
            max_ai=20        # Keep last 20 AI conversation messages
        )
        
        # Clear buffer after successful save
        if success:
            self._conversation_buffer.clear()
        
        return success
    
    def get_conversation_context(self, max_messages: int = 10) -> List[Dict]:
        """
        Get recent conversation context for the LLM.
        
        Args:
            max_messages: Maximum number of messages to return
            
        Returns:
            List of recent messages for context
        """
        # Combine buffer with stored memory
        memory = self._memory_manager.get_current_memory()
        stored_messages = memory.get("messages", [])
        
        # Combine and deduplicate
        all_messages = stored_messages + self._conversation_buffer
        
        # Remove duplicates while preserving order (include timestamp to avoid false duplicates)
        seen = set()
        unique_messages = []
        for msg in all_messages:
            # Include timestamp in key to avoid filtering legitimate repeated messages
            msg_key = f"{msg.get('role', '')}_{msg.get('content', '')}_{msg.get('timestamp', '')}"
            if msg_key not in seen:
                seen.add(msg_key)
                unique_messages.append(msg)
        
        # Return last N messages
        return unique_messages[-max_messages:]
    
    def process_message(self, user_message: str) -> str:
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The user's input message
            
        Returns:
            str: The AI's response
        """
        # Add user message to memory
        self.add_to_memory({
            "role": "user",
            "content": user_message,
            "type": "ai"
        })
        
        # Get conversation context
        context = self.get_conversation_context()
        
        # Prepare messages for LLM
        llm_messages = []
        
        # Add system message with user context
        system_message = {
            "role": "system",
            "content": f"You are a helpful AI assistant for {self.user.username}. "
                      f"You have access to their conversation history and should maintain context. "
                      f"Be personalized and remember previous interactions."
        }
        llm_messages.append(system_message)
        
        # Add conversation context
        for msg in context:
            if msg.get("type") == "ai" or "role" in msg:
                llm_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        # Add current message if not already in context
        if not any(msg.get("content") == user_message for msg in context):
            llm_messages.append({
                "role": "user",
                "content": user_message
            })
        
        try:
            # Generate response using LLM
            response = self._llm.invoke(llm_messages)
            
            # Extract response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Add response to memory
            self.add_to_memory({
                "role": "assistant",
                "content": response_text,
                "type": "ai"
            })
            
            return response_text
            
        except Exception as e:
            error_msg = f"I encountered an error: {str(e)}"
            self.add_to_memory({
                "role": "assistant",
                "content": error_msg,
                "type": "ai",
                "error": True
            })
            return error_msg
    
    def get_user_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the user's conversation history.
        
        Returns:
            Dict containing user conversation statistics
        """
        stats = self._memory_manager.get_memory_stats()
        stats["username"] = self.user.username
        stats["buffer_size"] = len(self._conversation_buffer)
        return stats
    
    def clear_conversation_buffer(self) -> None:
        """Clear the temporary conversation buffer."""
        self._conversation_buffer = []
    
    def clear_all_memory(self) -> bool:
        """
        Clear all conversation memory for this user.
        
        Returns:
            bool: True if successful, False otherwise
        """
        self._conversation_buffer = []
        return self._memory_manager.clear_memory()
    
    def export_conversation(self, format: str = "json") -> Any:
        """
        Export the user's conversation history.
        
        Args:
            format: Export format ('json', 'text')
            
        Returns:
            Exported data in requested format
        """
        memory_data = self._memory_manager.export_memory(include_metadata=True)
        
        if format == "text":
            # Convert to readable text format
            lines = []
            lines.append(f"Conversation History for {self.user.username}")
            lines.append("=" * 50)
            
            for msg in memory_data.get("messages", []):
                timestamp = msg.get("timestamp", "")
                role = msg.get("role", msg.get("sender", "unknown"))
                content = msg.get("content", "")
                lines.append(f"[{timestamp}] {role}: {content}")
            
            return "\n".join(lines)
        else:
            # Return as JSON
            return memory_data
    
    def search_memory(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search through conversation memory for specific content.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of matching messages
        """
        memory = self._memory_manager.get_current_memory()
        all_messages = memory.get("messages", [])
        
        # Simple text search (can be enhanced with embeddings later)
        query_lower = query.lower()
        matches = []
        
        for msg in all_messages:
            content = msg.get("content", "").lower()
            if query_lower in content:
                matches.append(msg)
                if len(matches) >= max_results:
                    break
        
        return matches
    
    def get_conversation_summary(self) -> str:
        """
        Generate a summary of the conversation history.
        
        Returns:
            str: Summary of conversation topics and key points
        """
        # Get recent messages
        messages = self.get_conversation_context(max_messages=20)
        
        if not messages:
            return "No conversation history available."
        
        # Simple summary (can be enhanced with LLM summarization)
        summary_parts = []
        summary_parts.append(f"Conversation with {self.user.username}")
        summary_parts.append(f"Total messages: {len(messages)}")
        
        # Extract topics (simple keyword extraction)
        topics = set()
        for msg in messages:
            content = msg.get("content", "").lower()
            # Extract potential topics (words > 4 chars)
            words = content.split()
            for word in words:
                if len(word) > 4 and word.isalpha():
                    topics.add(word)
        
        if topics:
            summary_parts.append(f"Topics discussed: {', '.join(list(topics)[:5])}")
        
        return " | ".join(summary_parts)
    
    def __repr__(self) -> str:
        """String representation of the agent."""
        stats = self.get_user_stats()
        return (f"<UserAgent(user={self.user.username}, "
                f"messages={stats['total_messages']}, "
                f"buffer={stats['buffer_size']})>")
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"AI Agent for {self.user.username}"
