"""Chat agent implementation."""
from typing import Dict, Any, Optional, List, Type, TypeVar, Union, Callable, Awaitable
from datetime import datetime, timezone
import json
import logging

from chat_agent.core.base_agent import BaseAgent, StateT
from chat_agent.core.state import State

# Type aliases
MessageHandler = Callable[[str, Dict[str, Any], 'ChatAgent'], Awaitable[Dict[str, Any]]]

# Type variable for the state class to support different state implementations
StateT = TypeVar('StateT', bound=State)

class ChatAgent(BaseAgent[StateT]):
    """A conversational agent that can process messages and maintain conversation state.
    
    This class extends BaseAgent with chat-specific functionality like message routing,
    conversation history management, and tool integration.
    """
    
    def __init__(
        self,
        state_class: Type[StateT] = State,  # type: ignore
        initial_state: Optional[StateT] = None,
        system_prompt: Optional[str] = None,
        message_handlers: Optional[Dict[str, MessageHandler]] = None,
        **kwargs
    ):
        """Initialize the chat agent.
        
        Args:
            state_class: The State class to use for managing conversation state.
            initial_state: Optional initial state to use. If not provided, a new state will be created.
            system_prompt: Optional system prompt to initialize the conversation with.
            message_handlers: Optional dictionary of message type to handler functions.
            **kwargs: Additional keyword arguments to pass to the parent class.
        """
        super().__init__(state_class=state_class, initial_state=initial_state, **kwargs)
        
        # Initialize message handlers
        self.message_handlers: Dict[str, MessageHandler] = message_handlers or {}
        
        # Set up default system prompt if provided
        if system_prompt:
            self.add_message("system", system_prompt)
    
    async def process_message(
        self,
        message: str,
        sender: str = "user",
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process an incoming message and generate a response.
        
        Args:
            message: The message text to process.
            sender: The sender of the message (e.g., 'user', 'assistant').
            message_type: The type of message (e.g., 'text', 'command').
            metadata: Optional metadata to include with the message.
            **kwargs: Additional keyword arguments for message processing.
            
        Returns:
            A dictionary containing the response and any additional data.
        """
        # Add the incoming message to the conversation history
        self.add_message(sender, message, message_type=message_type, **(metadata or {}))
        
        # Get the appropriate handler for the message type
        handler = self.message_handlers.get(message_type, self._default_message_handler)
        
        try:
            # Process the message with the handler
            response = await handler(message, metadata or {}, self)
            
            # If the handler returned a response, add it to the conversation
            if response and "response" in response:
                self.add_message("assistant", response["response"], **response.get("metadata", {}))
            
            return response or {}
            
        except Exception as e:
            # Log the error and return an error response
            error_msg = f"Error processing message: {str(e)}"
            logging.error(error_msg, exc_info=True)
            
            # Add error to conversation history
            self.add_message("system", error_msg, is_error=True)
            
            return {
                "response": "Sorry, I encountered an error processing your message.",
                "error": str(e),
                "success": False
            }
    
    async def _default_message_handler(
        self,
        message: str,
        metadata: Dict[str, Any],
        agent: 'ChatAgent'
    ) -> Dict[str, Any]:
        """Default message handler for text messages.
        
        Args:
            message: The message text to process.
            metadata: Additional message metadata.
            agent: Reference to the agent instance.
            
        Returns:
            A dictionary containing the response and any additional data.
        """
        # Default implementation just echoes the message back
        return {
            "response": f"Echo: {message}",
            "metadata": {"handled_by": "default_handler"}
        }
    
    def add_message_handler(self, message_type: str, handler: MessageHandler) -> None:
        """Register a message handler for a specific message type.
        
        Args:
            message_type: The message type to handle.
            handler: The handler function to register.
        """
        self.message_handlers[message_type] = handler
    
    def remove_message_handler(self, message_type: str) -> bool:
        """Remove a message handler for a specific message type.
        
        Args:
            message_type: The message type to remove the handler for.
            
        Returns:
            True if a handler was removed, False otherwise.
        """
        if message_type in self.message_handlers:
            del self.message_handlers[message_type]
            return True
        return False
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get the conversation history.
        
        Args:
            limit: Optional limit on the number of messages to return.
            
        Returns:
            A list of message dictionaries.
        """
        messages = self.state.messages
        if limit is not None and limit > 0:
            return messages[-limit:]
        return messages
    
    def clear_conversation(self) -> None:
        """Clear the conversation history while preserving the system message and other state."""
        # Keep only system messages
        system_messages = [msg for msg in self.state.messages if msg.get("role") == "system"]
        self.state.messages = system_messages
        self.state.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the agent to a dictionary."""
        data = super().to_dict()
        data.update({
            "message_handlers": list(self.message_handlers.keys()),
            "has_system_prompt": any(
                msg.get("role") == "system" 
                for msg in self.state.messages
            )
        })
        return data
