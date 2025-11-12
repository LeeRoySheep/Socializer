"""
Secure memory management system for user conversations.

Handles storage, retrieval, and management of encrypted conversation memory
with support for both AI conversations and general chat messages.

Author: Socializer Development Team
Date: 2024-11-12
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from memory.memory_encryptor import UserMemoryEncryptor


class SecureMemoryManager:
    """
    Manages encrypted conversation memory for a specific user.
    
    Features:
    - User-specific encryption
    - Separate tracking of AI conversations and general chat
    - Message limit enforcement
    - Automatic memory persistence
    
    Attributes:
        _user: User object
        _data_manager: DataManager instance for persistence
        _encryptor: UserMemoryEncryptor for this user
        _current_memory: In-memory cache of decrypted conversation
    """
    
    def __init__(self, data_manager, user):
        """
        Initialize the memory manager for a specific user.
        
        Args:
            data_manager: DataManager instance for database operations
            user: User object with encryption key
        """
        self._user = user
        self._data_manager = data_manager
        self._encryptor = UserMemoryEncryptor(user)
        self._current_memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """
        Load and decrypt existing memory from database.
        
        Returns:
            Dict containing decrypted memory or empty structure
        """
        try:
            # Get encrypted memory from database
            encrypted_memory = self._data_manager.get_user_memory(self._user.id)
            
            if encrypted_memory and self._encryptor.is_encrypted(encrypted_memory):
                # Decrypt the memory
                return self._encryptor.decrypt_memory(encrypted_memory)
            else:
                # Return empty memory structure
                return self._initialize_empty_memory()
                
        except Exception as e:
            print(f"Error loading memory for user {self._user.id}: {e}")
            return self._initialize_empty_memory()
    
    def _initialize_empty_memory(self) -> Dict[str, Any]:
        """
        Create an empty memory structure.
        
        Returns:
            Dict with empty memory structure
        """
        return {
            "messages": [],
            "general_chat": [],
            "ai_conversation": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "user_id": self._user.id,
                "version": "1.0"
            }
        }
    
    def save_conversation_memory(self, messages: List[Dict], max_messages: int = 20) -> bool:
        """
        Save conversation messages to encrypted memory.
        
        Args:
            messages: List of message dictionaries
            max_messages: Maximum number of messages to keep
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update current memory
            self._current_memory["messages"] = messages[-max_messages:] if len(messages) > max_messages else messages
            self._current_memory["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Encrypt and save
            encrypted = self._encryptor.encrypt_memory(self._current_memory)
            
            # Save to database
            success = self._data_manager.update_user_memory(self._user.id, encrypted)
            
            return success
            
        except Exception as e:
            print(f"Error saving memory for user {self._user.id}: {e}")
            return False
    
    def save_combined_memory(self, 
                           all_messages: List[Dict],
                           max_general: int = 10, 
                           max_ai: int = 20) -> bool:
        """
        Save both general chat and AI conversation messages.
        
        Args:
            all_messages: Combined list of all message types
            max_general: Maximum general chat messages to keep
            max_ai: Maximum AI conversation messages to keep
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # SECURITY: Filter out internal system prompts BEFORE saving
            filtered_messages = []
            blocked_count = 0
            
            for msg in all_messages:
                content = str(msg.get('content', ''))
                
                # Check if this is an internal system prompt
                if any(phrase in content for phrase in [
                    'CONVERSATION MONITORING REQUEST',
                    'INSTRUCTIONS:',
                    'Should you intervene',
                    'NO_INTERVENTION_NEEDED',
                    'You are monitoring this conversation',
                    'Analyze if intervention is needed'
                ]):
                    blocked_count += 1
                    continue  # Skip this message
                
                filtered_messages.append(msg)
            
            if blocked_count > 0:
                print(f"[SECURITY] Blocked {blocked_count} internal system prompts from encrypted memory for user {self._user.id}")
            
            # Separate message types from filtered messages
            general_messages = []
            ai_messages = []
            
            for msg in filtered_messages:
                msg_type = msg.get("type", "ai")
                if msg_type == "chat" or msg_type == "general":
                    general_messages.append(msg)
                else:
                    ai_messages.append(msg)
            
            # Apply limits
            self._current_memory["general_chat"] = general_messages[-max_general:] if len(general_messages) > max_general else general_messages
            self._current_memory["ai_conversation"] = ai_messages[-max_ai:] if len(ai_messages) > max_ai else ai_messages
            
            # Also update combined messages list (use filtered messages!)
            self._current_memory["messages"] = filtered_messages[-(max_general + max_ai):]
            
            # Update metadata
            self._current_memory["metadata"]["last_updated"] = datetime.now().isoformat()
            self._current_memory["metadata"]["message_counts"] = {
                "general": len(self._current_memory["general_chat"]),
                "ai": len(self._current_memory["ai_conversation"]),
                "total": len(self._current_memory["messages"])
            }
            
            # Encrypt and save
            encrypted = self._encryptor.encrypt_memory(self._current_memory)
            
            # Save to database
            success = self._data_manager.update_user_memory(self._user.id, encrypted)
            
            return success
            
        except Exception as e:
            print(f"Error saving combined memory for user {self._user.id}: {e}")
            return False
    
    def recall_conversation_memory(self) -> Optional[Dict[str, Any]]:
        """
        Recall and decrypt conversation memory.
        
        Returns:
            Dict containing conversation memory or None if error
        """
        try:
            # Try to get fresh from database
            encrypted_memory = self._data_manager.get_user_memory(self._user.id)
            
            if encrypted_memory and self._encryptor.is_encrypted(encrypted_memory):
                self._current_memory = self._encryptor.decrypt_memory(encrypted_memory)
            
            return self._current_memory
            
        except Exception as e:
            print(f"Error recalling memory for user {self._user.id}: {e}")
            return None
    
    def get_current_memory(self) -> Dict[str, Any]:
        """
        Get the current in-memory cache.
        
        Returns:
            Dict containing current memory state
        """
        return self._current_memory.copy()
    
    def add_message(self, message: Dict, message_type: str = "ai") -> None:
        """
        Add a single message to memory.
        
        Args:
            message: Message dictionary
            message_type: Type of message ('ai', 'general', 'chat')
        """
        # SECURITY: Filter out internal monitoring/system prompts
        # These should NEVER be saved to encrypted user memory
        content = str(message.get('content', ''))
        
        if any(phrase in content for phrase in [
            'CONVERSATION MONITORING REQUEST',
            'INSTRUCTIONS:',
            'Should you intervene',
            'NO_INTERVENTION_NEEDED',
            'You are monitoring this conversation',
            'Analyze if intervention is needed'
        ]):
            print(f"[SECURITY] Blocked internal system prompt from encrypted memory for user {self._user.id}")
            return  # Do NOT save this message
        
        # Add to messages list
        self._current_memory["messages"].append(message)
        
        # Add to specific category
        if message_type in ["chat", "general"]:
            self._current_memory["general_chat"].append(message)
        else:
            self._current_memory["ai_conversation"].append(message)
        
        # Update timestamp
        self._current_memory["metadata"]["last_updated"] = datetime.now().isoformat()
    
    def clear_memory(self) -> bool:
        """
        Clear all conversation memory for this user.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Reset to empty memory
            self._current_memory = self._initialize_empty_memory()
            
            # Save empty memory (encrypted)
            encrypted = self._encryptor.encrypt_memory(self._current_memory)
            success = self._data_manager.update_user_memory(self._user.id, encrypted)
            
            return success
            
        except Exception as e:
            print(f"Error clearing memory for user {self._user.id}: {e}")
            return False
    
    def get_last_messages(self, count: int = 10, message_type: Optional[str] = None) -> List[Dict]:
        """
        Get the last N messages, optionally filtered by type.
        
        Args:
            count: Number of messages to retrieve
            message_type: Optional filter ('ai', 'general', None for all)
            
        Returns:
            List of message dictionaries
        """
        if message_type == "general" or message_type == "chat":
            messages = self._current_memory.get("general_chat", [])
        elif message_type == "ai":
            messages = self._current_memory.get("ai_conversation", [])
        else:
            messages = self._current_memory.get("messages", [])
        
        return messages[-count:] if len(messages) > count else messages
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current memory.
        
        Returns:
            Dict containing memory statistics
        """
        return {
            "user_id": self._user.id,
            "total_messages": len(self._current_memory.get("messages", [])),
            "general_chat_count": len(self._current_memory.get("general_chat", [])),
            "ai_conversation_count": len(self._current_memory.get("ai_conversation", [])),
            "last_updated": self._current_memory.get("metadata", {}).get("last_updated"),
            "memory_version": self._current_memory.get("metadata", {}).get("version", "1.0")
        }
    
    def export_memory(self, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Export memory for backup or analysis (decrypted).
        
        Args:
            include_metadata: Whether to include metadata
            
        Returns:
            Dict containing exportable memory
            
        Note:
            This returns DECRYPTED data - handle with care!
        """
        export_data = {
            "messages": self._current_memory.get("messages", []),
            "general_chat": self._current_memory.get("general_chat", []),
            "ai_conversation": self._current_memory.get("ai_conversation", [])
        }
        
        if include_metadata:
            export_data["metadata"] = self._current_memory.get("metadata", {})
        
        return export_data
    
    def import_memory(self, memory_data: Dict[str, Any], merge: bool = False) -> bool:
        """
        Import memory from external source.
        
        Args:
            memory_data: Memory data to import
            merge: If True, merge with existing; if False, replace
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if merge:
                # Merge with existing memory
                existing = self._current_memory.get("messages", [])
                imported = memory_data.get("messages", [])
                self._current_memory["messages"] = existing + imported
                
                # Merge other categories
                for key in ["general_chat", "ai_conversation"]:
                    if key in memory_data:
                        existing = self._current_memory.get(key, [])
                        self._current_memory[key] = existing + memory_data[key]
            else:
                # Replace memory
                self._current_memory = memory_data
                self._current_memory["metadata"]["imported_at"] = datetime.now().isoformat()
            
            # Save to database
            encrypted = self._encryptor.encrypt_memory(self._current_memory)
            return self._data_manager.update_user_memory(self._user.id, encrypted)
            
        except Exception as e:
            print(f"Error importing memory for user {self._user.id}: {e}")
            return False
    
    def __repr__(self) -> str:
        """String representation of the memory manager."""
        stats = self.get_memory_stats()
        return f"<SecureMemoryManager(user_id={self._user.id}, messages={stats['total_messages']})>"
