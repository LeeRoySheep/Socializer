"""
Memory Handler with OTE Compliance

LOCATION: app/agents/memory_handler.py
PURPOSE: Manage encrypted conversation memory with OTE tracking

TRACE POINTS:
    - SAVE: Save conversation to memory
    - RECALL: Retrieve conversation history
    - EXTRACT_USER: Extract user message
    - EXTRACT_AI: Extract AI response
    - PERSIST: Persist to database

DEPENDENCIES:
    - memory.user_agent (UserAgent)
    
OTE COMPLIANCE:
    - Observability: All memory operations logged with timing
    - Traceability: Trace markers for save/recall flow
    - Evaluation: Success rates, persistence metrics
"""

import json
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, AIMessage

from app.utils import get_logger, observe, traceable, evaluate

# Get logger for this module
logger = get_logger(__name__)


class MemoryHandler:
    """
    Encrypted conversation memory handler with OTE tracking.
    
    Manages saving and retrieving conversation history with encryption.
    All operations are tracked for observability and performance monitoring.
    
    OTE Compliance:
        - All operations observed with timing
        - Trace markers show save/recall flow
        - Success/failure rates tracked
        - Persistence metrics monitored
    
    Attributes:
        memory_agent: UserAgent instance for encrypted memory management
        conversation_tool: ConversationRecallTool for retrieving history
    
    Example:
        >>> handler = MemoryHandler(memory_agent, conversation_tool)
        >>> handler.save_conversation(state, response)
        💾 Conversation saved to encrypted memory
        >>> history = handler.get_conversation_history(user_id)
        >>> print(len(history))
        15
    """
    
    def __init__(self, memory_agent: Any, conversation_tool: Any):
        """
        Initialize MemoryHandler.
        
        Args:
            memory_agent: UserAgent instance for memory management
            conversation_tool: ConversationRecallTool for retrieving history
        """
        logger.trace("INIT", "Initializing MemoryHandler")
        
        self.memory_agent = memory_agent
        self.conversation_tool = conversation_tool
        
        logger.observe(
            "init_complete",
            has_memory_agent=bool(memory_agent),
            has_conversation_tool=bool(conversation_tool)
        )
    
    @observe("save_conversation")
    @evaluate(detect_anomalies=True)
    def save_conversation(self, state: Dict, response: Dict) -> None:
        """
        Save conversation messages to encrypted user memory.
        
        TRACE PATH:
            SAVE → EXTRACT_USER → EXTRACT_AI → PERSIST
        
        This method extracts user and AI messages from the conversation state
        and saves them to encrypted memory storage. Called automatically after
        each conversation turn.
        
        Args:
            state: Current conversation state containing messages
            response: Response dictionary containing AI messages
            
        Returns:
            None: Performs side effects only (saves to memory)
            
        Raises:
            No exceptions raised - errors are caught and logged
        """
        logger.trace("SAVE", "Starting conversation save")
        
        try:
            messages = state.get("messages", [])
            
            # TRACE POINT 1: Extract user message
            user_saved = self._extract_and_save_user_message(messages)
            
            # TRACE POINT 2: Extract AI response
            ai_saved = self._extract_and_save_ai_response(response)
            
            # TRACE POINT 3: Persist to database
            if user_saved or ai_saved:
                logger.trace("PERSIST", "Persisting messages to encrypted storage")
                self.memory_agent.save_memory()
                logger.info("💾 Conversation saved to encrypted memory")
                logger.observe(
                    "save_complete",
                    user_saved=user_saved,
                    ai_saved=ai_saved,
                    success=True
                )
            else:
                logger.warning("No messages extracted for saving")
                logger.observe("save_complete", user_saved=False, ai_saved=False, success=False)
                
        except Exception as e:
            logger.error(f"⚠️ Error saving to memory: {e}", exc_info=True)
            logger.observe("save_complete", success=False, error=str(e))
    
    @traceable()
    def _extract_and_save_user_message(self, messages: List) -> bool:
        """
        Extract and save user message from conversation state.
        
        TRACE PATH:
            EXTRACT_USER → Find HumanMessage → Add to memory
        
        Searches backwards through messages to find the most recent user message.
        Handles multiple message formats (HumanMessage, dict, objects).
        
        Args:
            messages: List of messages in conversation
            
        Returns:
            bool: True if user message found and saved, False otherwise
        """
        logger.trace("EXTRACT_USER", f"Searching {len(messages)} messages for user input")
        
        # Search backwards for user message
        for msg in reversed(messages):
            # LangChain HumanMessage with type attribute
            if hasattr(msg, 'type') and msg.type == 'human':
                content = getattr(msg, 'content', '')
                if content:
                    self.memory_agent.add_to_memory({
                        "role": "user",
                        "content": content,
                        "type": "ai"  # Marks as AI conversation
                    })
                    logger.trace("EXTRACT_USER", f"Saved HumanMessage: {content[:50]}...")
                    return True
            
            # Dict format
            elif isinstance(msg, dict) and msg.get('role') == 'user':
                content = msg.get('content', '')
                if content:
                    self.memory_agent.add_to_memory({
                        "role": "user",
                        "content": content,
                        "type": "ai"
                    })
                    logger.trace("EXTRACT_USER", f"Saved dict user message: {content[:50]}...")
                    return True
            
            # HumanMessage class (fallback)
            elif hasattr(msg, '__class__') and msg.__class__.__name__ == 'HumanMessage':
                content = msg.content
                if content:
                    self.memory_agent.add_to_memory({
                        "role": "user",
                        "content": content,
                        "type": "ai"
                    })
                    logger.trace("EXTRACT_USER", f"Saved HumanMessage: {content[:50]}...")
                    return True
        
        logger.warning("No user message found in state")
        return False
    
    @traceable()
    def _extract_and_save_ai_response(self, response: Dict) -> bool:
        """
        Extract and save AI response messages.
        
        TRACE PATH:
            EXTRACT_AI → Find AIMessage → Add to memory
        
        Extracts AI messages from response, skipping tool calls.
        Only saves final response content.
        
        Args:
            response: Response dictionary containing messages
            
        Returns:
            bool: True if AI message found and saved, False otherwise
        """
        logger.trace("EXTRACT_AI", "Extracting AI response messages")
        
        if not response or 'messages' not in response:
            logger.warning("No messages in response")
            return False
        
        saved_count = 0
        for msg in response['messages']:
            # Dict format
            if isinstance(msg, dict) and 'content' in msg:
                content = msg.get('content', '')
                if content:
                    self.memory_agent.add_to_memory({
                        "role": msg.get('role', 'assistant'),
                        "content": content,
                        "type": "ai"
                    })
                    saved_count += 1
                    logger.trace("EXTRACT_AI", f"Saved dict AI response: {content[:50]}...")
            
            # AIMessage object (skip if it has tool calls)
            elif hasattr(msg, 'content'):
                # Check if it has tool_calls and they're not empty
                has_tool_calls = (hasattr(msg, 'tool_calls') and 
                                msg.tool_calls and 
                                len(msg.tool_calls) > 0)
                
                if not has_tool_calls:
                    content = getattr(msg, 'content', '')
                    if content:
                        self.memory_agent.add_to_memory({
                            "role": "assistant",
                            "content": content,
                            "type": "ai"
                        })
                        saved_count += 1
                        logger.trace("EXTRACT_AI", f"Saved AIMessage: {content[:50]}...")
        
        if saved_count > 0:
            logger.observe("ai_messages_extracted", count=saved_count)
            return True
        else:
            logger.warning("No AI messages extracted")
            return False
    
    @observe("get_conversation_history")
    @traceable()
    def get_conversation_history(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a user.
        
        TRACE PATH:
            RECALL → Call tool → Parse result → Return history
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of conversation messages, empty list on error
        """
        logger.trace("RECALL", f"Retrieving history for user_id={user_id}")
        
        try:
            # Call conversation recall tool
            result = self.conversation_tool._run(user_id)
            
            if result:
                # Parse result (may be dict or JSON string)
                result_data = result if isinstance(result, dict) else json.loads(result)
                
                if result_data.get("status") == "success" and "data" in result_data:
                    history = result_data["data"]
                    logger.observe(
                        "recall_complete",
                        user_id=user_id,
                        messages=len(history),
                        success=True
                    )
                    return history
            
            logger.warning(f"No history found for user_id={user_id}")
            logger.observe("recall_complete", user_id=user_id, messages=0, success=True)
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
            logger.observe("recall_complete", user_id=user_id, success=False, error=str(e))
            return []
    
    @traceable()
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory stats
        """
        try:
            stats = {
                "has_memory_agent": bool(self.memory_agent),
                "has_conversation_tool": bool(self.conversation_tool)
            }
            
            # Try to get buffer size if available
            if hasattr(self.memory_agent, 'memory_buffer'):
                stats["buffer_size"] = len(self.memory_agent.memory_buffer)
            
            return stats
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}
    
    @traceable()
    def clear_buffer(self) -> bool:
        """
        Clear the memory buffer without saving.
        
        Useful for testing or error recovery.
        
        Returns:
            bool: True if cleared successfully
        """
        try:
            if hasattr(self.memory_agent, 'memory_buffer'):
                self.memory_agent.memory_buffer.clear()
                logger.info("Memory buffer cleared")
                return True
            return False
        except Exception as e:
            logger.error(f"Error clearing buffer: {e}")
            return False
