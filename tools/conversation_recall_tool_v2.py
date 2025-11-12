"""
Enhanced Conversation Recall Tool that uses the new memory system.

This version integrates with the encrypted memory storage to recall
both AI conversations and general chat messages.

Author: Socializer Development Team
Date: 2024-11-12
"""

import json
from typing import Type, Optional, Dict, Any

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from datamanager.data_manager import DataManager
from memory.secure_memory_manager import SecureMemoryManager


class ConversationRecallInput(BaseModel):
    """Input schema for conversation recall operation."""
    
    user_id: int = Field(
        ..., 
        description="The ID of the user whose conversation to retrieve",
        gt=0
    )


class ConversationRecallToolV2(BaseTool):
    """
    Enhanced tool to recall conversations from encrypted memory.
    
    This tool retrieves conversation history from the user's encrypted
    memory storage, including both AI conversations and general chat messages.
    """
    
    name: str = "recall_last_conversation"
    description: str = (
        "Use this tool to recall the user's conversation history from memory. "
        "This includes both AI conversations and general chat messages where the user participated. "
        "Returns the last 10 messages from memory. "
        "Use this when the user asks about previous conversations, context, or what they discussed. "
        "Input should be a user_id."
    )
    args_schema: Type[BaseModel] = ConversationRecallInput
    dm: Optional[DataManager] = None

    def __init__(self, data_manager: DataManager):
        """Initialize the ConversationRecallToolV2."""
        super().__init__()
        self.dm = data_manager

    def _run(self, *args, **kwargs) -> str:
        """Execute the conversation retrieval operation."""
        # Handle both direct call and tool call formats
        if args and isinstance(args[0], dict):
            user_id = args[0].get("user_id")
        elif "user_id" in kwargs:
            user_id = kwargs["user_id"]
        elif args:
            user_id = args[0]
        else:
            return json.dumps({
                "status": "error", 
                "message": "user_id is required"
            })

        if not user_id:
            return json.dumps({
                "status": "error", 
                "message": "user_id is required"
            })

        # Call the actual implementation
        return self._get_conversation_from_memory(user_id)

    def invoke(self, *args, **kwargs) -> str:
        """LangChain compatibility method for tool invocation."""
        return self._run(*args, **kwargs)

    def _get_conversation_from_memory(self, user_id: int) -> str:
        """
        Retrieve conversation from encrypted memory storage.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            JSON string containing conversation history
        """
        try:
            # Get the user
            user = self.dm.get_user(user_id)
            
            if not user:
                return json.dumps({
                    "status": "error",
                    "message": f"User {user_id} not found"
                })
            
            # Create secure memory manager for this user
            memory_manager = SecureMemoryManager(self.dm, user)
            
            # Recall conversation memory
            memory_data = memory_manager.recall_conversation_memory()
            
            if not memory_data:
                return json.dumps({
                    "status": "success",
                    "message": "No conversation memory found",
                    "data": [],
                    "general_chat": [],
                    "ai_conversation": []
                })
            
            # Extract different types of messages
            all_messages = memory_data.get("messages", [])
            general_chat = memory_data.get("general_chat", [])
            ai_conversation = memory_data.get("ai_conversation", [])
            
            # Get last 10 of each type
            recent_messages = all_messages[-10:] if len(all_messages) > 10 else all_messages
            recent_general = general_chat[-10:] if len(general_chat) > 10 else general_chat
            recent_ai = ai_conversation[-10:] if len(ai_conversation) > 10 else ai_conversation
            
            # Count message types
            ai_count = sum(1 for msg in recent_messages 
                          if isinstance(msg, dict) and msg.get('type') == 'ai')
            chat_count = sum(1 for msg in recent_messages 
                           if isinstance(msg, dict) and msg.get('type') in ['chat', 'general'])
            
            return json.dumps({
                "status": "success",
                "message": "Conversation retrieved from encrypted memory",
                "data": recent_messages,
                "general_chat": recent_general,
                "ai_conversation": recent_ai,
                "total_messages": len(all_messages),
                "returned_messages": len(recent_messages),
                "ai_messages": ai_count,
                "chat_messages": chat_count,
                "metadata": memory_data.get("metadata", {})
            })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to retrieve conversation from memory: {str(e)}",
            })


# Create a backward-compatible alias
ConversationRecallTool = ConversationRecallToolV2
