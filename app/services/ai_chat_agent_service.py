"""Service for managing AI chat agent instances."""
import asyncio
import logging
from typing import Dict, Optional, AsyncGenerator, Any

from ai_chatagent import AiChatagent, ChatSession
from datamanager.data_model import User

logger = logging.getLogger(__name__)

class AIChatAgentService:
    """Service for managing AI chat agent instances."""
    
    def __init__(self):
        """Initialize the AI chat agent service."""
        self.sessions: Dict[int, ChatSession] = {}
    
    def get_session(self, user: User) -> ChatSession:
        """
        Get or create a chat session for a user.
        
        Args:
            user: The user to get a session for
            
        Returns:
            ChatSession: The chat session for the user
        """
        if user.id not in self.sessions:
            logger.info(f"Creating new chat session for user {user.username} (ID: {user.id})")
            try:
                # Try to create a session with minimal requirements
                self.sessions[user.id] = ChatSession(user_id=user.id)
            except ValueError as e:
                logger.warning(f"Failed to create chat session: {str(e)}. Creating a test user session.")
                # Create a minimal user object for testing
                from datamanager.data_model import User as UserModel
                test_user = UserModel(
                    id=user.id,
                    username=user.username or f"testuser_{user.id}",
                    hashed_email=f"test_{user.id}@example.com",
                    hashed_password="testpassword",
                    is_active=True,
                    role="user"
                )
                # Create a session with the test user
                self.sessions[user.id] = ChatSession(user_id=user.id, username=test_user.username)
                
        return self.sessions[user.id]
    
    async def process_message(
        self,
        user: User,
        message: str
    ) -> str:
        """
        Process a message using the user's chat agent.
        
        Args:
            user: The user sending the message
            message: The message to process
            
        Returns:
            str: The AI's response
        """
        try:
            session = self.get_session(user)
            response = session.process_message(message)
            return response
        except Exception as e:
            logger.error(f"Error processing message for user {user.id}: {str(e)}", exc_info=True)
            return "I'm sorry, I encountered an error processing your message. Please try again later."
    
    def clear_session(self, user_id: int) -> None:
        """
        Clear a user's chat session.
        
        Args:
            user_id: The ID of the user
        """
        if user_id in self.sessions:
            logger.info(f"Clearing chat session for user ID: {user_id}")
            del self.sessions[user_id]
            
    async def get_response(self, user_id: int, message: str, chat_history: list) -> str:
        """
        Get a response from the AI chat agent.
        
        Args:
            user_id: The ID of the user
            message: The user's message
            chat_history: The chat history
            
        Returns:
            str: The AI's response
        """
        try:
            logger.info(f"Getting AI response for user {user_id}")
            
            # Create a minimal user object with the required attributes
            from datamanager.data_model import User as UserModel
            user = UserModel(
                id=user_id,
                username=f"user_{user_id}",
                hashed_email=f"user_{user_id}@example.com",
                hashed_password="",
                is_active=True,
                role="user"
            )
            
            # Use the process_message method to get a response
            response = await asyncio.get_event_loop().run_in_executor(
                None,  # Use default executor (thread pool)
                lambda: self.process_message(user, message)
            )
            
            logger.debug(f"Generated response for user {user_id}: {response}")
            return response
            
        except Exception as e:
            logger.error(f"Error getting AI response: {str(e)}", exc_info=True)
            return "I'm sorry, I'm having trouble generating a response right now. Please try again later."

# Create a singleton instance
ai_chat_agent_service = AIChatAgentService()
