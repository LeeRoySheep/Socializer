"""Service for managing chat agent instances."""
import logging
from typing import Dict, Optional, Any, AsyncGenerator
from chat_agent.core.chat_agent import ChatAgent
from chat_agent.core.state import State
from datamanager.data_model import User

logger = logging.getLogger(__name__)

class ChatAgentService:
    """Service for managing chat agent instances."""
    
    def __init__(self):
        """Initialize the chat agent service."""
        self.agents: Dict[str, ChatAgent] = {}
        self.system_prompt = """
        You are a helpful AI assistant in a chat application. 
        Be friendly, concise, and helpful in your responses.
        Keep your responses relatively short and conversational.
        If asked about your capabilities, mention that you can help with general questions,
        provide information, and assist with using the chat application.
        """
    
    def get_agent(self, user_id: str) -> ChatAgent:
        """
        Get or create a chat agent for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            ChatAgent: The chat agent instance for the user
        """
        if user_id not in self.agents:
            # Create a new agent with default state
            agent = ChatAgent(
                system_prompt=self.system_prompt,
                initial_state=State(
                    user_id=user_id,
                    conversation_history=[],
                    preferences={}
                )
            )
            self.agents[user_id] = agent
            logger.info(f"Created new chat agent for user {user_id}")
        
        return self.agents[user_id]
    
    async def process_message(
        self, 
        user_id: str, 
        message: str,
        message_type: str = "user"
    ) -> Dict[str, Any]:
        """
        Process a message using the user's chat agent.
        
        Args:
            user_id: The ID of the user sending the message
            message: The message content
            message_type: The type of message (e.g., "user", "system")
            
        Returns:
            Dict[str, Any]: Response from the chat agent
        """
        agent = self.get_agent(user_id)
        
        # Process the message
        response = await agent.process_message(
            message=message,
            sender="user",
            message_type=message_type
        )
        
        # Format the response
        return {
            "type": "chat",
            "sender": "assistant",
            "message": response.get("response", "I'm sorry, I couldn't process your message."),
            "is_self": False,
            "is_ai": True
        }
    
    async def process_message_stream(
        self, 
        user_id: str, 
        message: str,
        message_type: str = "user"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process a message using the user's chat agent and stream the response.
        
        Args:
            user_id: The ID of the user sending the message
            message: The message content
            message_type: The type of message (e.g., "user", "system")
            
        Yields:
            Dict[str, Any]: Response chunks from the chat agent
        """
        # For now, we'll just call the non-streaming version and yield a single chunk
        # In a real implementation, this would stream the response token by token
        response = await self.process_message(user_id, message, message_type)
        yield {"content": response["message"]}
    
    def clear_agent(self, user_id: str) -> None:
        """
        Clear a user's chat agent.
        
        Args:
            user_id: The ID of the user
        """
        if user_id in self.agents:
            del self.agents[user_id]
            logger.info(f"Cleared chat agent for user {user_id}")

# Create a singleton instance
chat_agent_service = ChatAgentService()
