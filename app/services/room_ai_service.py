"""
Room AI Service

Handles AI responses in private chat rooms.
The AI helps with:
- Detecting language barriers
- Improving empathy
- Identifying misunderstandings
- Natural conversation facilitation
"""

import logging
from typing import Optional, List, Dict
import asyncio
from concurrent.futures import ThreadPoolExecutor

from datamanager.data_manager import DataManager
from datamanager.data_model import User, ChatRoom, RoomMessage

logger = logging.getLogger(__name__)

# Thread pool for running AI agent (which is synchronous)
executor = ThreadPoolExecutor(max_workers=3)


class RoomAIService:
    """
    Service for AI responses in private rooms.
    
    The AI monitors conversations and responds when:
    - It detects language barriers
    - Users show lack of empathy
    - There are clear misunderstandings
    - Users explicitly ask for help
    """
    
    def __init__(self, dm: DataManager):
        """
        Initialize the room AI service.
        
        Args:
            dm: DataManager instance
        """
        self.dm = dm
    
    async def should_ai_respond(
        self,
        room: ChatRoom,
        recent_messages: List[RoomMessage],
        new_message: RoomMessage
    ) -> bool:
        """
        Determine if AI should respond to a message.
        
        Args:
            room: The chat room
            recent_messages: Recent messages in the room
            new_message: The newly sent message
            
        Returns:
            bool: True if AI should respond
        """
        if not room.ai_enabled:
            return False
        
        content = new_message.content.lower()
        
        # Respond if directly mentioned
        if any(trigger in content for trigger in ['@ai', 'ai,', 'hey ai', 'ai help']):
            logger.info("AI triggered by direct mention")
            return True
        
        # Respond if detecting potential issues
        # Language barriers
        if any(word in content for word in ['not understand', "don't understand", 'what mean', 'translate']):
            logger.info("AI triggered by language barrier")
            return True
        
        # Empathy issues
        if any(word in content for word in ['rude', 'offensive', 'hurt', 'upset', 'angry']):
            logger.info("AI triggered by potential empathy issue")
            return True
        
        # Questions
        if '?' in content and len(content) > 20:
            # Only respond to some questions to avoid being too chatty
            # Let's say 30% chance for general questions
            import random
            if random.random() < 0.3:
                logger.info("AI triggered by question")
                return True
        
        # Otherwise, don't respond (let users chat naturally)
        return False
    
    async def generate_room_response(
        self,
        room: ChatRoom,
        sender: User,
        message_content: str,
        recent_messages: List[RoomMessage]
    ) -> Optional[str]:
        """
        Generate AI response for a room message.
        
        Args:
            room: The chat room
            sender: User who sent the message
            message_content: Content of the message
            recent_messages: Recent messages for context
            
        Returns:
            Optional[str]: AI response or None if error
        """
        try:
            # Build context from recent messages
            conversation_context = self._build_conversation_context(
                room, recent_messages
            )
            
            # Create prompt for AI
            prompt = self._create_room_prompt(
                room, sender, message_content, conversation_context
            )
            
            # Get AI response (run in thread pool since AI agent is synchronous)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                executor,
                self._get_ai_response,
                sender,
                prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None
    
    def _build_conversation_context(
        self,
        room: ChatRoom,
        recent_messages: List[RoomMessage]
    ) -> str:
        """
        Build conversation context from recent messages.
        
        Args:
            room: The chat room
            recent_messages: Recent messages
            
        Returns:
            str: Formatted conversation context
        """
        context_lines = []
        
        for msg in recent_messages[-10:]:  # Last 10 messages
            if msg.sender_type == "ai":
                sender_name = "AI Assistant"
            elif msg.sender_id:
                user = self.dm.get_user(msg.sender_id)
                sender_name = user.username if user else "Unknown"
            else:
                sender_name = "System"
            
            context_lines.append(f"{sender_name}: {msg.content}")
        
        return "\n".join(context_lines)
    
    def _create_room_prompt(
        self,
        room: ChatRoom,
        sender: User,
        message_content: str,
        conversation_context: str
    ) -> str:
        """
        Create prompt for AI agent.
        
        Args:
            room: The chat room
            sender: User who sent the message
            message_content: Content of the message
            conversation_context: Recent conversation
            
        Returns:
            str: Formatted prompt
        """
        # Get room members
        members = self.dm.get_room_members(room.id)
        member_names = []
        for member in members:
            if member.user_id and member.role != 'ai':
                user = self.dm.get_user(member.user_id)
                if user:
                    member_names.append(user.username)
        
        room_name = room.name or f"Chat with {', '.join(member_names)}"
        
        prompt = f"""You are in a private group chat called "{room_name}" with {len(member_names)} users: {', '.join(member_names)}.

Your role is to help users communicate better by:
1. Detecting and helping with language barriers
2. Encouraging empathy and understanding
3. Clarifying misunderstandings
4. Being supportive but not intrusive

Recent conversation:
{conversation_context}

{sender.username} just said: {message_content}

Respond naturally and helpfully. Keep your response concise (1-3 sentences). Only respond if you can genuinely help."""
        
        return prompt
    
    def _get_ai_response(self, user: User, prompt: str) -> str:
        """
        Get AI response (synchronous, runs in thread pool).
        
        Args:
            user: User object (for AI agent initialization)
            prompt: Prompt for AI
            
        Returns:
            str: AI response
        """
        try:
            # Import here to avoid circular imports
            from ai_chatagent import AiChatagent
            from llm_manager import LLMManager
            from llm_config import LLMSettings
            
            # Initialize LLM
            llm = LLMManager.get_llm(
                provider=LLMSettings.DEFAULT_PROVIDER,
                model=LLMSettings.DEFAULT_MODEL,
                temperature=0.7,  # Slightly more creative for conversation
                max_tokens=LLMSettings.DEFAULT_MAX_TOKENS
            )
            
            # Create AI agent
            agent = AiChatagent(user, llm)
            graph = agent.build_graph()
            
            # Get response
            config = {"configurable": {"thread_id": f"room_{user.id}"}}
            response = graph.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config
            )
            
            # Extract AI message
            if response and "messages" in response:
                for msg in reversed(response["messages"]):
                    if hasattr(msg, 'content') and msg.content:
                        return msg.content
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return None


# Global instance
_room_ai_service: Optional[RoomAIService] = None


def get_room_ai_service() -> RoomAIService:
    """
    Get the global RoomAIService instance.
    
    Returns:
        RoomAIService: Global service instance
    """
    global _room_ai_service
    if _room_ai_service is None:
        dm = DataManager("data.sqlite.db")
        _room_ai_service = RoomAIService(dm)
    return _room_ai_service
