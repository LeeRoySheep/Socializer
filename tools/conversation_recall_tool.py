"""
Conversation Recall Tool

This module provides functionality to retrieve conversation history from memory
for a specific user. It's designed to be used as a LangChain tool in AI chat systems.

Classes:
    ConversationRecallInput: Input validation schema
    ConversationRecallTool: Tool for retrieving conversation history

Author: Socializer Development Team
Date: 2025-10-14
"""

import json
from typing import Type, Optional, Dict, Any

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from datamanager.data_manager import DataManager


class ConversationRecallInput(BaseModel):
    """
    Input schema for conversation recall operation.
    
    This model validates and structures the input parameters required
    to retrieve conversation history for a specific user.
    
    Attributes:
        user_id (int): The unique identifier for the user whose conversation
                      history should be retrieved. Must be a positive integer.
    
    Example:
        >>> input_data = ConversationRecallInput(user_id=123)
        >>> print(input_data.user_id)
        123
    """
    
    user_id: int = Field(
        ..., 
        description="The ID of the user whose conversation to retrieve",
        gt=0  # Greater than 0
    )


class ConversationRecallTool(BaseTool):
    """
    Tool to recall the last conversation from memory.
    
    This tool retrieves conversation history for a specific user from the database,
    returning the most recent messages (up to 5) to provide context for ongoing
    conversations. It's designed to be used within a LangChain tool ecosystem.
    
    Attributes:
        name (str): Tool identifier - "recall_last_conversation"
        description (str): Human-readable tool description for AI agents
        args_schema (Type[BaseModel]): Input validation schema
        dm (DataManager): Database manager instance for data operations
    
    Methods:
        _run(*args, **kwargs) -> str:
            Main execution method, handles various input formats
        
        invoke(*args, **kwargs) -> str:
            LangChain compatibility wrapper
        
        _get_conversation(user_id: int) -> str:
            Core implementation for conversation retrieval
    
    Returns:
        str: JSON-formatted string containing:
            - status (str): "success" or "error"
            - message (str): Descriptive status message
            - data (list): List of conversation messages (up to 5)
            - total_messages (int): Total number of messages (on success)
    
    Example:
        >>> from datamanager.data_manager import DataManager
        >>> dm = DataManager("database.db")
        >>> tool = ConversationRecallTool(data_manager=dm)
        >>> result = tool.invoke(user_id=1)
        >>> print(result)
        {"status": "success", "data": [...], "total_messages": 10}
    
    Notes:
        - Returns only the last 5 messages to keep context manageable
        - Handles multiple input formats for flexibility
        - Gracefully handles errors and missing data
        - Thread-safe when used with proper DataManager session handling
    """
    
    name: str = "recall_last_conversation"
    description: str = (
        "Use this tool to recall the user's conversation history from memory. "
        "This includes both AI conversations and general chat messages where the user participated. "
        "Use this when the user asks about previous conversations, context, or what they discussed. "
        "Input should be a user_id."
    )
    args_schema: Type[BaseModel] = ConversationRecallInput
    dm: Optional[DataManager] = None

    def __init__(self, data_manager: DataManager):
        """
        Initialize the ConversationRecallTool.
        
        Args:
            data_manager (DataManager): Instance of DataManager for database operations
        
        Raises:
            TypeError: If data_manager is not a DataManager instance
        
        Example:
            >>> dm = DataManager("database.db")
            >>> tool = ConversationRecallTool(data_manager=dm)
        """
        super().__init__()
        self.dm = data_manager

    def _run(self, *args, **kwargs) -> str:
        """
        Execute the conversation retrieval operation.
        
        This method handles multiple input formats for flexibility:
        - Dictionary: {"user_id": 1}
        - Keyword argument: user_id=1
        - Positional argument: 1
        
        Args:
            *args: Positional arguments (user_id or dict)
            **kwargs: Keyword arguments (user_id)
        
        Returns:
            str: JSON string with format:
                {
                    "status": "success" | "error",
                    "message": "Status description",
                    "data": [...],  # List of messages (on success)
                    "total_messages": int  # Total count (on success)
                }
        
        Examples:
            >>> tool._run({"user_id": 1})
            '{"status": "success", "data": [...]}'
            
            >>> tool._run(user_id=1)
            '{"status": "success", "data": [...]}'
            
            >>> tool._run(1)
            '{"status": "success", "data": [...]}'
        
        Notes:
            - Missing user_id returns error status
            - Database errors are caught and returned as error status
            - JSON parsing errors are handled gracefully
        """
        # Handle both direct call and tool call formats
        if args and isinstance(args[0], dict):
            # Called with a single dict argument (from tool call)
            user_id = args[0].get("user_id")
        elif "user_id" in kwargs:
            # Called with user_id keyword argument
            user_id = kwargs["user_id"]
        elif args:
            # Called with user_id as a positional argument
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
        return self._get_conversation(user_id)

    def invoke(self, *args, **kwargs) -> str:
        """
        LangChain compatibility method for tool invocation.
        
        This method is called by LangChain's tool system and serves as a
        wrapper around the _run method to maintain compatibility with
        LangChain's tool execution framework.
        
        Args:
            *args: Positional arguments passed to _run
            **kwargs: Keyword arguments passed to _run
        
        Returns:
            str: JSON string result from _run method
        
        Example:
            >>> result = tool.invoke(user_id=1)
            >>> print(result)
            {"status": "success", ...}
        """
        return self._run(*args, **kwargs)

    def _get_conversation(self, user_id: int) -> str:
        """
        Core implementation of conversation retrieval.
        
        Retrieves conversation history from the database for a specific user
        and formats it as a JSON response. Returns only the last 5 messages
        to keep the context manageable while providing relevant history.
        
        Args:
            user_id (int): The unique identifier of the user
        
        Returns:
            str: JSON string containing:
                Success case:
                {
                    "status": "success",
                    "message": "Conversation retrieved successfully",
                    "data": [
                        {"role": "user", "content": "..."},
                        {"role": "assistant", "content": "..."}
                    ],
                    "total_messages": 10
                }
                
                No messages case:
                {
                    "status": "success",
                    "message": "No previous conversation found",
                    "data": []
                }
                
                Error case:
                {
                    "status": "error",
                    "message": "Error description"
                }
        
        Raises:
            No exceptions are raised; all errors are caught and returned
            as JSON error responses.
        
        Example:
            >>> result = tool._get_conversation(user_id=1)
            >>> data = json.loads(result)
            >>> print(data["status"])
            success
        
        Notes:
            - Returns maximum 5 most recent messages
            - Handles both string and list message formats
            - Gracefully handles JSON parsing errors
            - Database errors are caught and reported
        """
        try:
            # Retrieve user from database
            user = self.dm.get_user(user_id)
            
            # Handle user not found or no messages
            if not user or not user.messages or user.messages == "[]":
                return json.dumps({
                    "status": "success",
                    "message": "No previous conversation found",
                    "data": [],
                })

            # Parse the messages if they're stored as a JSON string
            try:
                if isinstance(user.messages, str):
                    messages = json.loads(user.messages)
                else:
                    messages = user.messages

                # Ensure messages is a list
                if not isinstance(messages, list):
                    messages = []

                # Return the last 10 messages to include both AI and chat history
                last_messages = messages[-10:] if len(messages) > 10 else messages
                
                # Count message types for context
                ai_count = sum(1 for msg in last_messages if isinstance(msg, dict) and msg.get('type') == 'ai')
                chat_count = sum(1 for msg in last_messages if isinstance(msg, dict) and msg.get('type') == 'chat')
                
                return json.dumps({
                    "status": "success",
                    "message": "Conversation retrieved successfully",
                    "data": last_messages,
                    "total_messages": len(messages),
                    "returned_messages": len(last_messages),
                    "ai_messages": ai_count,
                    "chat_messages": chat_count
                })

            except json.JSONDecodeError as e:
                # Handle corrupted message data
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to parse conversation: {str(e)}",
                    "data": [],
                })

        except Exception as e:
            # Handle any other errors (database, etc.)
            return json.dumps({
                "status": "error",
                "message": f"Failed to retrieve conversation: {str(e)}",
            })
