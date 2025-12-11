"""
AI Chat Agent Module
====================

This module provides the core AI chat agent functionality for the Socializer application.
It implements a sophisticated conversational AI that helps users improve their social skills
and communication abilities.

Main Components:
    - AiChatagent: Main chat agent class with state graph architecture
    - UserPreferenceTool: Manages user preferences with encryption
    - LifeEventTool: Tracks and manages user life events
    - CommunicationClarificationTool: Translates and clarifies messages
    - Conversation memory system with encryption
    - Automatic language detection and adaptation
    - Multi-provider LLM support (OpenAI, Gemini, Claude)

Features:
    - State-based conversation management using LangGraph
    - Secure encrypted memory per user
    - Automatic language detection and user preference saving
    - Tool loop prevention
    - Empathy monitoring and intervention
    - Social skills tracking and evaluation
    - Life event tracking with emotional context

Design Patterns:
    - State Pattern: Conversation state management
    - Strategy Pattern: Multiple LLM providers
    - Singleton Pattern: DataManager, LLMManager
    - Factory Pattern: Tool creation and management
    - Observer Pattern: Memory and event tracking

Architecture:
    The agent uses a graph-based architecture where:
    1. User message enters the system
    2. Language is auto-detected if not set
    3. System prompt is generated with context
    4. LLM processes message and may call tools
    5. Tool results are processed
    6. Final response is generated
    7. Conversation is saved to encrypted memory

Usage:
    >>> user = dm.get_user(user_id)
    >>> agent = AiChatagent(user=user, llm=llm)
    >>> graph = agent.build_graph()
    >>> response = graph.invoke({"messages": [HumanMessage(content="Hello")]})

Dependencies:
    - langchain: LLM framework
    - langgraph: State graph management
    - pydantic: Data validation
    - cryptography: Memory encryption

Author: Socializer Development Team
Version: 2.0
Date: 2024-11-12
"""

import atexit
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Union, TypedDict, Annotated

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage, HumanMessage
from langchain_tavily import TavilySearch
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import add_messages, StateGraph, END
from pydantic import BaseModel, Field, field_validator
from response_formatter import ResponseFormatter
from format_tool import FormatTool

# Import extracted tools
from tools.conversation_recall_tool import ConversationRecallTool
from tools.gemini.search_tool import SearchTool  # New Gemini-compatible SearchTool
from tools.gemini import GeminiResponseHandler  # Response handler for empty responses
from tools.tool_manager import ToolManager  # Universal tool manager for all LLM providers
from services.ai_language_detector import AILanguageDetector, LanguageConfidence  # AI-based language detection
from tools.language_preference_tool import LanguagePreferenceTool  # Language preference management

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import local modules after adding project root to path
from datamanager.data_manager import DataManager
from datamanager.data_model import User, Training, UserSkill
from datamanager.life_event_manager import LifeEventManager, LifeEventModel
from app.config import SQLALCHEMY_DATABASE_URL
from app.ote_logger import get_logger, create_metrics
import time

# Memory system imports
from memory.user_agent import UserAgent
from memory.secure_memory_manager import SecureMemoryManager

# Import extracted tools (modularized)
from tools.user import UserPreferenceTool
from tools.skills import SkillEvaluator
from tools.search import TavilySearchTool
from tools.events import LifeEventTool
from tools.communication import ClarifyCommunicationTool, CulturalStandardsChecker

# Import training system
from training import TrainingPlanManager

# Import extracted handlers (modularized)
from app.agents import ResponseHandler, ToolHandler, MemoryHandler
from app.agents.local_model_cleaner import LocalModelCleaner

# Initialize the database manager
db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', ''
)
dm = DataManager(db_path)

# Initialize tools
try:
    from skill_agents import (
        get_evaluation_orchestrator,
        stop_evaluation_orchestrator,
        SkillEvaluationOrchestrator,
    )
    SKILL_AGENTS_AVAILABLE = True
except ImportError:
    print("Warning: skill_agents module not found. Some features may be limited.")
    SKILL_AGENTS_AVAILABLE = False

# Import LLM Manager for flexible model switching
from llm_manager import LLMManager
from llm_config import LLMSettings

# set API KEYS
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")

# Initialize LLM using LLM Manager (configured in llm_config.py)
llm = LLMManager.get_llm(
    provider=LLMSettings.DEFAULT_PROVIDER,
    model=LLMSettings.DEFAULT_MODEL,
    temperature=LLMSettings.DEFAULT_TEMPERATURE,
    max_tokens=LLMSettings.DEFAULT_MAX_TOKENS
)

print(f"🤖 LLM initialized: {LLMSettings.DEFAULT_PROVIDER} - {LLMSettings.DEFAULT_MODEL}")

tool_1 = TavilySearch(max_results=10)

# Initialize global TrainingPlanManager
training_plan_manager = TrainingPlanManager(dm)

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from typing import Type


# ConversationRecallTool has been extracted to tools/conversation_recall_tool.py


# ==============================================================================
# TOOL INSTANTIATION  
# ==============================================================================
# All tool classes have been extracted to tools/ directory.
# We instantiate them here for use in the agent.
#
# Extracted Tools:
#   - UserPreferenceTool → tools/user/preference_tool.py
#   - SkillEvaluator → tools/skills/evaluator_tool.py
#   - TavilySearchTool → tools/search/tavily_search_tool.py
#   - LifeEventTool → tools/events/life_event_tool.py
#   - ClarifyCommunicationTool → tools/communication/clarity_tool.py
# ==============================================================================

# Legacy Tavily search (keep for compatibility)
tavily_search_tool = tool_1

# Instantiate extracted tools
conversation_recall = ConversationRecallTool(dm)
skill_evaluator = SkillEvaluator(dm)
user_preference_tool = UserPreferenceTool(dm)
life_event_tool = LifeEventTool(dm)
clarify_tool = ClarifyCommunicationTool()
cultural_checker = CulturalStandardsChecker()
format_tool = FormatTool()

# Combine all tools for agent
tools = [
    tavily_search_tool,
    conversation_recall,
    skill_evaluator,
    user_preference_tool,
    life_event_tool,
    clarify_tool,
    cultural_checker,
    format_tool
]

memory = InMemorySaver()


class State(TypedDict):
    """
    create State class to keep track of chat
    """

    messages: Annotated[list, add_messages]


# BasicToolNode class removed - now using ToolHandler from app.agents
# ToolHandler provides the same functionality with full OTE integration
# Alias for backwards compatibility
BasicToolNode = ToolHandler


class UserData:
    def __init__(
        self,
        username,
        hashed_password,
        role="User",
        skills=None,
        training=None,
        preferences=None,
        temperature=0.7,
    ):
        self.username = username
        self.hashed_password = hashed_password
        self.role = role
        self.preferences = preferences or {}
        self.temperature = temperature
        self.skills = skills
        self.training = training


tool_node = BasicToolNode(tools=tools)


graph_builder = StateGraph(State)


class AiChatagent:
    """
    AI Chat Agent for Social Skills Coaching.
    
    This class implements a sophisticated conversational AI agent that helps users
    improve their social skills, communication abilities, and emotional intelligence.
    It uses a state-graph architecture to manage conversations, tools, and memory.
    
    Key Responsibilities:
        - Manage user conversations with context and memory
        - Provide social skills coaching and empathy guidance
        - Auto-detect and adapt to user's preferred language
        - Track life events and emotional context
        - Monitor conversations for empathy and understanding
        - Prevent tool call loops and infinite recursion
        - Log and track LLM usage and costs
    
    Architecture:
        Uses LangGraph for state management with these nodes:
        - chatbot: Main conversation processing
        - tools: Tool execution (search, memory recall, etc.)
        - __end__: Conversation termination
    
    Attributes:
        user (User): The user object from database
        llm: Language model instance (OpenAI, Gemini, or Claude)
        preferences (dict): User preferences dictionary
        temperature (float): LLM temperature setting (default: 0.7)
        user_language (str): User's preferred language
        language_confirmed (bool): Whether language preference is confirmed
        language_detector: Language detection service instance
        user_profile (dict): Complete user profile with skills and preferences
        memory_agent (UserAgent): Encrypted memory management agent
        ote_logger: Observability logger for metrics and costs
        conversation_tool (ConversationRecallTool): Memory recall tool
        preference_tool (UserPreferenceTool): User preference management
        life_event_tool (LifeEventTool): Life event tracking
        clarify_tool (CommunicationClarificationTool): Translation/clarification
        
    Design Patterns:
        - State Pattern: Graph-based conversation state
        - Strategy Pattern: Multiple LLM providers
        - Facade Pattern: Simplifies complex tool interactions
        - Observer Pattern: Memory and event tracking
    
    Example:
        >>> user = dm.get_user(user_id)
        >>> llm = LLMManager.get_llm("openai", "gpt-4o-mini")
        >>> agent = AiChatagent(user=user, llm=llm)
        >>> graph = agent.build_graph()
        >>> response = graph.invoke({
        ...     "messages": [HumanMessage(content="Help me with empathy")]
        ... })
        >>> print(response['messages'][-1].content)
    
    Thread Safety:
        Not thread-safe. Create separate instances for concurrent users.
    
    Performance:
        - Average response time: 1-3 seconds
        - Memory per instance: ~50MB
        - Encrypted memory: Per-user isolation
    
    Notes:
        - Automatically saves conversations to encrypted memory
        - Detects and prevents tool call loops (max 2 calls per tool)
        - Supports 14+ languages with auto-detection
        - Logs all LLM calls for cost tracking
    """

    def __init__(self, user: User, llm):
        """
        Initialize AI Chat Agent for a specific user.
        
        This constructor sets up the complete agent infrastructure including:
        - User profile and preferences
        - Language detection and preference loading
        - Encrypted memory system
        - Tool instances (search, recall, preferences, etc.)
        - LLM provider detection and tool management
        - Observability logging
        
        The initialization process:
        1. Loads user data (skills, training, preferences)
        2. Detects/loads user's preferred language
        3. Initializes encrypted memory agent
        4. Creates tool instances
        5. Detects LLM provider and configures tools accordingly
        6. Sets up observability logging
        
        Args:
            user (User): User object from database with id, username, preferences
            llm: Language model instance (ChatOpenAI, ChatGoogleGenerativeAI, etc.)
                Must have either model_name or model attribute
        
        Raises:
            ValueError: If user is None or invalid
            AttributeError: If LLM doesn't have required attributes
            
        Side Effects:
            - Loads memory from database
            - Prints initialization status to console
            - Sets up logging infrastructure
        
        Example:
            >>> from datamanager.data_manager import DataManager
            >>> from llm_manager import LLMManager
            >>> dm = DataManager("data.sqlite.db")
            >>> user = dm.get_user(user_id=5)
            >>> llm = LLMManager.get_llm("openai", "gpt-4o-mini")
            >>> agent = AiChatagent(user=user, llm=llm)
            🌐 User language preference: German (saved)
            🧠 Memory system initialized for user: testuser
            🔧 Detected LLM provider: openai
        
        Notes:
            - Each agent instance is user-specific and not thread-safe
            - Memory is encrypted per-user with unique encryption keys
            - Language detection happens automatically on first message if not set
            - Tools are configured based on detected LLM provider
        """
        self.user = user
        self.preferences = user.preferences or {}
        self.temperature = user.temperature or 0.7
        self.llm = llm  # Store original LLM without tools
        
        # ✅ Initialize O-T-E Logger for observability
        self.ote_logger = get_logger()
        self.request_start_time = None
        self.current_request_id = None
        self.skills = dm.get_skills_for_user(user.id) or {}
        self.training = dm.get_training_for_user(user.id) or {}
        
        # ✅ Load user's preferred language from database
        user_prefs = dm.get_user_preferences(user.id, preference_type="communication")
        self.user_language = user_prefs.get("communication.preferred_language", None)
        self.language_confirmed = self.user_language is not None
        
        # Initialize AI-based language detector
        self.language_detector = AILanguageDetector(self.llm)
        
        if self.user_language:
            print(f"🌐 User language preference: {self.user_language} (saved)")
        else:
            self.user_language = "English"  # Default
            print(f"🌐 No language preference saved, will auto-detect from messages")
        
        self.user_profile = {
            "username": user.username,
            "skills": self.skills,
            "training": self.training,
            "preferences": self.preferences,
            "temperature": self.temperature,
            "language": self.user_language,
        }
        self.used_tools_in_session = set()  # Track tools used in current session
        self.last_user_message = None  # Track the last user message to detect new conversations
        
        # Initialize memory system
        self.memory_agent = UserAgent(
            user=self.user,
            llm=self.llm,
            data_manager=dm
        )
        # Load existing memory context
        self.memory_agent._load_context()
        print(f"🧠 Memory system initialized for user: {user.username}")
        
        # ✅ Initialize training plan system
        self.training_manager = training_plan_manager
        self.training_plan = self.training_manager.get_or_create_training_plan(user)
        self.message_counter = self.training_plan.get("message_count", 0)
        print(f"🎯 Training plan loaded: {len(self.training_plan.get('trainings', {}))} active trainings")
        
        # Initialize tool instances
        self.tavily_search = TavilySearchTool(search_tool=tool_1)
        self.conversation_tool = ConversationRecallTool(dm)
        self.skill_evaluator_tool = SkillEvaluator(dm)
        self.user_preference_tool = UserPreferenceTool(dm)
        self.clarify_tool = ClarifyCommunicationTool()
        self.cultural_checker_tool = CulturalStandardsChecker()
        
        # ✅ self.tools will be generated from actual tool instances later
        # This ensures names always match what's bound to the LLM
        
        # ===================================================================
        # 🚀 NEW: Universal Tool Management (works with ALL LLM providers)
        # ===================================================================
        
        # Detect LLM provider from model name
        llm_model_name = getattr(llm, 'model_name', getattr(llm, 'model', ''))
        llm_class_name = llm.__class__.__name__
        
        # Determine provider
        if 'gemini' in str(llm_model_name).lower() or 'google' in llm_class_name.lower():
            provider = "gemini"
        elif 'claude' in str(llm_model_name).lower() or 'anthropic' in llm_class_name.lower():
            provider = "claude"
        elif 'gpt' in str(llm_model_name).lower() or 'openai' in llm_class_name.lower():
            provider = "openai"
        else:
            provider = "openai"  # Default fallback
        
        print(f"🔧 Detected LLM provider: {provider}")
        
        # ✅ Detect if using local model (LM Studio, Ollama)
        # Try multiple attribute names that different LangChain versions use
        self.llm_endpoint = ''
        for attr in ['base_url', 'openai_api_base', 'api_base', 'client']:
            val = getattr(llm, attr, None)
            if val:
                # Handle Pydantic URL objects
                if hasattr(val, 'unicode_string'):
                    self.llm_endpoint = val.unicode_string()
                elif hasattr(val, '__str__'):
                    val_str = str(val)
                    # Check if it looks like a URL
                    if 'localhost' in val_str or '127.0.0.1' in val_str or ':1234' in val_str or ':11434' in val_str:
                        self.llm_endpoint = val_str
                        break
                else:
                    self.llm_endpoint = str(val) if val else ''
                if self.llm_endpoint and ('localhost' in self.llm_endpoint or '127.0.0.1' in self.llm_endpoint):
                    break
        
        # Also check if the client has base_url
        if not self.llm_endpoint and hasattr(llm, 'client') and hasattr(llm.client, 'base_url'):
            self.llm_endpoint = str(llm.client.base_url)
        
        print(f"🔍 LLM endpoint detected: '{self.llm_endpoint}'")
        
        self.is_local_model = LocalModelCleaner.is_local_model(
            model_name=str(llm_model_name),
            endpoint=self.llm_endpoint
        )
        
        if self.is_local_model:
            print(f"🏠 Local model detected: {llm_model_name} at {self.llm_endpoint}")
        else:
            print(f"☁️  Cloud model detected: {llm_model_name}")
        
        # Initialize ToolManager for this provider
        self.tool_manager = ToolManager(provider=provider, data_manager=dm)
        
        # Get tools optimized for this provider
        managed_tools = self.tool_manager.get_tools()
        print(f"🔧 Loaded {len(managed_tools)} tools from ToolManager")
        
        # ===================================================================
        # Backward Compatibility: Keep old tool instances
        # (These will be gradually migrated to ToolManager)
        # ===================================================================
        
        # Initialize legacy tools that aren't yet in ToolManager
        self.tavily_search = TavilySearchTool(search_tool=tool_1)  # Legacy
        self.conversation_tool = ConversationRecallTool(dm)  # In ToolManager
        self.skill_evaluator_tool = SkillEvaluator(dm)  # TODO: Migrate
        self.user_preference_tool = UserPreferenceTool(dm)  # TODO: Migrate
        self.clarify_tool = ClarifyCommunicationTool()  # TODO: Migrate
        self.life_event_tool = LifeEventTool(dm) if 'dm' in globals() else None  # TODO: Migrate
        self.format_tool = FormatTool()  # TODO: Migrate
        self.language_preference_tool = LanguagePreferenceTool(dm, user.id)  # Language confirmation
        
        # Combine managed tools + legacy tools
        legacy_tools = [
            self.skill_evaluator_tool,
            self.user_preference_tool,
            self.clarify_tool,
            self.format_tool,
            self.language_preference_tool  # New tool for language confirmation
        ]
        if self.life_event_tool:
            legacy_tools.append(self.life_event_tool)
        
        # Final tool list (managed + legacy)
        tool_list = managed_tools + legacy_tools
        
        # Create mapping for backward compatibility
        self.tool_instances = {tool.name: tool for tool in tool_list}
        
        # ✅ Generate self.tools from actual tool instances (for logging/debugging)
        # This ensures names always match what's actually available
        self.tools = [
            {
                "name": tool.name,
                "description": tool.description if hasattr(tool, 'description') else ""
            }
            for tool in tool_list
        ]
        
        print(f"🔧 Total tools available: {len(tool_list)}")
        print(f"   Tool names: {list(self.tool_instances.keys())}")
        
        # ===================================================================
        # Bind tools to LLM
        # ===================================================================
        
        # Initialize response handler for empty responses
        # Initialize handlers with OTE integration
        self.response_handler = ResponseHandler()
        self.memory_handler = MemoryHandler(self.memory_agent, self.conversation_tool)
        
        try:
            # Bind all tools to LLM (works for all providers now!)
            self.llm_with_tools = llm.bind_tools(tool_list)
            print(f"✅ Successfully bound {len(tool_list)} tools to {provider} LLM")
        except Exception as e:
            print(f"⚠️  Tool binding failed: {e}")
            print(f"   Using LLM without tools")
            self.llm_with_tools = llm

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Retrieve the conversation history for this agent."""
        try:
            # Call the tool directly with the user's ID
            result = self.conversation_tool._run(self.user.id)
            if result:
                result_data = result if isinstance(result, dict) else json.loads(result)
                if (
                    result_data.get("status") == "success"
                    and "data" in result_data
                ):
                    return result_data["data"]
            return []
        except Exception as e:
            print(f"Error retrieving conversation history: {e}")
            return []

    def chatbot(self, state: State) -> dict:
        """
        Process user message and generate AI response with tool support.
        
        This is the main conversation processing method that handles the complete
        chat flow including language detection, tool execution, loop prevention,
        and response generation. It's called by the LangGraph state machine.
        
        Process Flow:
            1. Request tracing and logging initialization
            2. Input validation (check for valid state and messages)
            3. Language auto-detection for new users
            4. Tool call loop detection and prevention
            5. Tool execution handling (if applicable)
            6. AI response generation with context
            7. Memory saving
            8. Response return with metrics logging
        
        Key Features:
            - **Language Auto-Detection**: Automatically detects and saves user's
              preferred language on first message
            - **Loop Prevention**: Prevents infinite tool call loops by detecting
              duplicate tool calls (max 2 calls per tool per question)
            - **Tool Execution**: Handles tool calls and processes results
            - **Memory Management**: Saves conversations to encrypted memory
            - **Observability**: Logs all steps with request IDs and metrics
            - **Error Handling**: Graceful degradation on errors
        
        Args:
            state (State): LangGraph state dictionary containing:
                - messages (list): List of conversation messages
                  Can include HumanMessage, AIMessage, ToolMessage
                - Other state data passed through graph
        
        Returns:
            dict: State update with format:
                {
                    "messages": [AIMessage or dict with response]
                }
                
        Raises:
            No exceptions raised directly - all errors handled gracefully
            Returns error message dict on failures
        
        Side Effects:
            - Logs to OTE logger (request IDs, metrics, costs)
            - Saves conversation to encrypted memory
            - Updates user language preference if detected
            - Prints debug information to console
            - Modifies self.user_language if language detected
            - Modifies self.language_confirmed if language saved
        
        Example:
            >>> state = {
            ...     "messages": [
            ...         HumanMessage(content="Hallo! Wie geht es dir?")
            ...     ]
            ... }
            >>> response = agent.chatbot(state)
            🔍 Language detection: German (confidence: high)
            ✅ Auto-saved language preference: German
            >>> print(response['messages'][-1].content)
            "Hallo! Mir geht es gut, danke..."
        
        Tool Call Loop Prevention:
            The method prevents infinite loops by tracking tool calls:
            - Scopes detection to current question (since last HumanMessage)
            - Allows max 2 calls per unique (tool_name, args) pair
            - Excludes formatting tools from loop detection
            - Returns cached response if loop detected
            
            Example loop prevention:
            >>> # User asks: "What's the weather?"
            >>> # AI calls: tavily_search("weather")
            >>> # AI calls: tavily_search("weather") again
            >>> # Loop detected! Returns without 3rd call
        
        Language Detection:
            Automatically detects language if not yet confirmed:
            - Only triggers on first HumanMessage
            - Requires text length > 5 characters
            - Auto-saves if confidence > 90%
            - Asks user if confidence 70-90%
            - Uses default (English) if confidence < 70%
        
        Performance:
            - Average execution time: 1-3 seconds
            - With tool calls: 2-5 seconds
            - Memory overhead: ~10MB per request
            - Logs all timing metrics
        
        Thread Safety:
            Not thread-safe. Each user should have their own agent instance.
        
        Notes:
            - Called automatically by LangGraph state machine
            - Should not be called directly in normal usage
            - All conversation state is immutable (new dict returned)
            - Memory is automatically saved after response
            - Request ID is generated for tracing
        
        See Also:
            - build_graph(): Creates the state graph that calls this method
            - _get_ai_response(): Generates the actual AI response
            - _save_to_memory(): Saves conversation to encrypted storage
        """
        # ✅ O-T-E: Start request tracing
        self.current_request_id = self.ote_logger.generate_request_id()
        self.request_start_time = time.time()
        
        try:
            print("\n=== CHATBOT METHOD START ===")
            
            # ✅ O-T-E: Log request start
            self.ote_logger.logger.info(
                f"🚀 Chat request started",
                extra={
                    'request_id': self.current_request_id,
                    'user_id': self.user.id,
                    'event_type': 'request_start'
                }
            )
            
            # Validate input state
            if not state or "messages" not in state or not state["messages"]:
                print("ERROR: Invalid or empty message state")
                return {"messages": [{"role": "assistant", "content": "I couldn't process your message. Please try again."}]}
            
            messages = state["messages"]
            print(f"Processing {len(messages)} messages")
            last_message = messages[-1]
            print(f"Last message type: {type(last_message).__name__}")
            
            # ✅ TRAINING: Increment message count for user messages
            should_check_training = False
            if hasattr(last_message, 'type') and last_message.type == 'human':
                self.message_counter += 1
                self.training_manager.increment_message_count(self.user)
                print(f"📊 Message count: {self.message_counter}")
                
                # Check every 5th message for training progress
                if self.message_counter % 5 == 0:
                    should_check_training = True
                    print(f"🎯 Training progress check triggered (message #{self.message_counter})")
            
            # ✅ AI-BASED LANGUAGE DETECTION (if not yet confirmed)
            detected_language_info = None
            if not self.language_confirmed and hasattr(last_message, 'type') and last_message.type == 'human':
                user_text = getattr(last_message, 'content', '')
                if user_text and len(user_text) > 5:  # Meaningful text
                    print(f"🤖 Using AI to detect language from: {user_text[:50]}...")
                    result = self.language_detector.detect(user_text)
                    print(f"🔍 AI detected language: {result.language} (confidence: {result.confidence.value}, score: {result.confidence_score:.2f})")
                    
                    if self.language_detector.should_auto_save(result):
                        # Very high confidence (>90%) - auto-save without asking
                        print(f"✅ High confidence ({result.confidence_score:.2f}) - calling language preference tool")
                        # Let AI use the tool to save it
                        detected_language_info = {
                            'language': result.language,
                            'confidence': result.confidence_score,
                            'should_ask': False,
                            'auto_save': True
                        }
                    else:
                        # Medium/low confidence - AI should ask in detected language
                        print(f"⚠️  Medium/low confidence ({result.confidence_score:.2f}) - AI will ask for confirmation")
                        detected_language_info = {
                            'language': result.language,
                            'confidence': result.confidence_score,
                            'should_ask': True,
                            'confirmation_message': result.confirmation_message or f"I detected you might prefer {result.language}. Is that correct?"
                        }
            
            # ✅ ENHANCED: Check for tool call loops (same tool called 2+ times)
            # BUT ONLY within the CURRENT user question (not across different questions)
            if len(messages) >= 3:
                # Find the last HumanMessage to scope to current question
                last_human_index = -1
                for i in range(len(messages) - 1, -1, -1):
                    if hasattr(messages[i], 'type') and messages[i].type == 'human':
                        last_human_index = i
                        break
                
                # Collect tool calls from CURRENT question only
                tool_calls_history = []
                messages_to_check = messages[last_human_index:] if last_human_index >= 0 else messages[-6:]
                for msg in messages_to_check:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tc in msg.tool_calls:
                            tool_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', '')
                            tool_args = tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', {})
                            tool_calls_history.append((tool_name, str(tool_args)))
                
                # ✅ Trigger if SAME tool call appears 2+ times (more aggressive)
                if len(tool_calls_history) >= 2:
                    # Count occurrences of each unique call
                    call_counts = {}
                    for call in tool_calls_history:
                        call_counts[call] = call_counts.get(call, 0) + 1
                    
                    # If any call appears 2+ times, stop the loop
                    # BUT exclude formatting/utility tools (these should never be blocked)
                    NEVER_LOOP_BLOCK = {'format_output', 'clarify_communication'}
                    
                    for call, count in call_counts.items():
                        if count >= 2:
                            tool_name = call[0]
                            
                            # Skip loop detection for formatting tools
                            if tool_name in NEVER_LOOP_BLOCK:
                                print(f"✅ {tool_name} called {count} times - ALLOWED (formatting tool)")
                                continue
                            
                            print(f"⚠️  Detected tool loop: {tool_name} called {count} times with same args, breaking...")
                            result = {"messages": [{"role": "assistant", 
                                              "content": f"I've already searched for that information. Based on the results I found, let me provide you with the answer."}]}
                            self.memory_handler.save_conversation(state, result)
                            return result
            
            # If last message is an AIMessage with tool_calls, check if already executed
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                print("\n" + "="*70)
                print("🔍 STEP 1: TOOL CALL DETECTION")
                print("="*70)
                print(f"📍 Current message index: {len(messages)}")
                print(f"📍 Total messages in state: {len(messages)}")
                
                # ✅ DEBUG: Show all messages in conversation
                print(f"\n📋 MESSAGE HISTORY:")
                for i, msg in enumerate(messages):
                    msg_type = type(msg).__name__
                    has_tools = hasattr(msg, 'tool_calls') and msg.tool_calls
                    print(f"   [{i}] {msg_type} | Has tool_calls: {has_tools}")
                    if has_tools:
                        for tc in msg.tool_calls:
                            tc_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', '?')
                            tc_args = tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', {})
                            print(f"       → Tool: {tc_name}({tc_args})")
                
                print(f"\n" + "="*70)
                print("🔍 STEP 2: COLLECTING PREVIOUS TOOL CALLS")
                print("="*70)
                
                # ✅ Collect all previous tool calls (name + args) from this conversation
                previous_calls = set()
                for i, msg in enumerate(messages[:-1]):  # All messages except the current one
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for prev_tc in msg.tool_calls:
                            prev_name = prev_tc.get('name') if isinstance(prev_tc, dict) else getattr(prev_tc, 'name', '')
                            prev_args = prev_tc.get('args') if isinstance(prev_tc, dict) else getattr(prev_tc, 'args', {})
                            call_signature = (prev_name, str(prev_args))
                            previous_calls.add(call_signature)
                            print(f"   [Msg {i}] Previous call: {prev_name}({prev_args})")
                
                print(f"\n📊 Total unique previous calls: {len(previous_calls)}")
                
                print(f"\n" + "="*70)
                print("🔍 STEP 3: CHECKING CURRENT TOOL CALL FOR DUPLICATES")
                print("="*70)
                
                # Check if current tool calls are duplicates
                for tool_call in last_message.tool_calls:
                    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                    tool_args = tool_call.get('args') if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
                    
                    print(f"\n   🎯 Current tool call: {tool_name}({tool_args})")
                    
                    # Check if this exact tool+args was already called
                    current_call = (tool_name, str(tool_args))
                    print(f"   🔎 Signature: {current_call}")
                    print(f"   🔎 In previous calls? {current_call in previous_calls}")
                    
                    if current_call in previous_calls:
                        print(f"\n   ⚠️  ⚠️  ⚠️  DUPLICATE DETECTED! ⚠️  ⚠️  ⚠️")
                        print(f"   🛑 Tool {tool_name} already called with same args")
                        print(f"   🛑 BLOCKING duplicate call")
                        print(f"   ✅ Will use previous results instead")
                        print("="*70 + "\n")
                        result = {"messages": [{"role": "assistant", 
                                          "content": f"I've already searched for that information. Based on the results I found earlier, let me provide you with the answer."}]}
                        self.memory_handler.save_conversation(state, result)
                        return result
                
                print(f"\n   ✅ NO DUPLICATES FOUND - This is a NEW tool call")
                print(f"\n" + "="*70)
                print("✅ STEP 4: APPROVING NEW TOOL CALL FOR EXECUTION")
                print("="*70 + "\n")
                return {"messages": [last_message]}
            
            # If last message is a ToolMessage, we need to process its result
            is_tool_result = hasattr(last_message, '__class__') and last_message.__class__.__name__ == 'ToolMessage'
            
            # Only process if last message is from user or is a tool result
            # If last message is AIMessage without tool_calls, this shouldn't be called
            if hasattr(last_message, '__class__'):
                msg_class = last_message.__class__.__name__
                if msg_class == 'AIMessage' and not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
                    print(f"\n=== SKIPPING: Already have AI response ===")
                    return {"messages": []}
            
            if is_tool_result:
                print("\n=== PROCESSING TOOL RESULTS ===")
                
                # For local models: Add explicit interpretation guidance
                if self.is_local_model:
                    # Find the ToolMessage content
                    tool_content = ""
                    original_query = ""
                    for msg in reversed(messages):
                        if isinstance(msg, ToolMessage):
                            tool_content = msg.content
                        elif isinstance(msg, HumanMessage):
                            original_query = msg.content
                            break
                    
                    if tool_content:
                        print(f"🔧 Local model: Enhancing tool result interpretation")
                        
                        # Check for empathy issue flags in tool result
                        empathy_issue = "EMPATHY_ISSUE_DETECTED" in tool_content or "TEACH_BETTER_COMMUNICATION" in tool_content
                        
                        if empathy_issue:
                            print(f"⚠️  EMPATHY ISSUE DETECTED - forcing coaching response")
                            
                            # Extract the original problematic text
                            problem_text = ""
                            if "original_text" in tool_content:
                                import re
                                match = re.search(r"original_text['\"]?\s*[:=]\s*['\"]?([^'\"}\n]+)", tool_content)
                                if match:
                                    problem_text = match.group(1).strip()
                            
                            interpretation_guide = SystemMessage(content=(
                                f"⛔ STOP! DO NOT GIVE A GENERIC GREETING!\n\n"
                                f"The user said something HURTFUL: \"{problem_text or 'see tool results'}\"\n\n"
                                f"You are a SOCIAL SKILLS COACH. Your response MUST:\n"
                                f"1. START by acknowledging you noticed the message was harsh\n"
                                f"2. EXPLAIN specifically why calling people 'stupid' is hurtful\n"
                                f"3. SUGGEST a better way: 'I'm frustrated' instead of insults\n"
                                f"4. Be kind - maybe they're having a bad day\n\n"
                                f"EXAMPLE RESPONSE:\n"
                                f"\"I noticed your greeting sounded a bit harsh. Calling people 'stupid' can really hurt feelings. "
                                f"If you're feeling frustrated, try saying 'I'm having a tough day' instead. "
                                f"How can I help you feel better?\"\n\n"
                                f"Respond in {self.user_language}. Output ONLY your coaching - NO 'Hello, how can I help?'"
                            ))
                        else:
                            interpretation_guide = SystemMessage(content=(
                                f"You received tool results. Provide a helpful coaching response in {self.user_language}.\n"
                                f"Focus on social skills and communication improvement.\n"
                                f"NO JSON output - just your natural response."
                            ))
                        messages = [interpretation_guide] + list(messages)
            else:
                print("\n=== PROCESSING REGULAR MESSAGE ===")
            
            # Load last 20 messages from database for context
            historical_messages = []
            try:
                result = self.conversation_tool._run(self.user.id)
                if result:
                    result_data = result if isinstance(result, dict) else json.loads(result)
                    if result_data.get("status") == "success" and "data" in result_data:
                        historical_messages = result_data["data"][-20:]  # Last 20 messages
                        print(f"✅ Loaded {len(historical_messages)} historical messages from database")
            except Exception as e:
                print(f"❌ Could not load historical messages: {e}")
            
            # Enhanced system message with social behavior training and translation
            language_status = "confirmed" if self.language_confirmed else "auto-detected (not yet confirmed)"
            system_prompt = f"""You are an AI Social Coach and Communication Assistant for user ID: {self.user.id} (Username: {self.user.username})

🌐 **USER'S PREFERRED LANGUAGE: {self.user_language}** (Status: {language_status})
⚠️ CRITICAL: You MUST ALWAYS respond in {self.user_language}.
- All your responses should be written entirely in {self.user_language}
- Adapt your tone and cultural context to {self.user_language} speakers
- When monitoring conversations, provide interventions in {self.user_language}

🔍 **LANGUAGE CONFIRMATION (for new users):**
- If language is NOT YET CONFIRMED, I will detect the user's language using AI
- When I detect their language with medium/low confidence:
  * I will ask them IN THEIR DETECTED LANGUAGE if that's correct
  * Example: If I detect German → Ask in German: "Möchten Sie auf Deutsch fortfahren?"
  * Example: If I detect Spanish → Ask in Spanish: "¿Prefieres continuar en español?"
- When the user confirms OR you are certain of their language:
  * Use the `set_language_preference` tool to save it
  * Args: language="German" (or Spanish, French, etc.), confirmed=True
  * This permanently saves their preference
- Always ask for language confirmation IN THE DETECTED LANGUAGE, not in English!

{self.training_manager.get_training_context_for_prompt(self.user)}

⚠️ **CRITICAL: ALWAYS PROVIDE A RESPONSE**
After receiving tool results, you MUST respond with helpful, informative content.
NEVER return empty responses. Always explain what you found and help the user.

🛡️ **PRIMARY ROLE: CONVERSATION MODERATOR & EMPATHY GUARDIAN**

**YOUR CORE MISSION:**
You are ALWAYS monitoring ALL conversations for:
1. **Misunderstandings** between users - detect and clarify IMMEDIATELY
2. **Lack of empathy** - gently intervene when someone is insensitive
3. **Cultural misunderstandings** - explain context and bridge cultural gaps
4. **Social context** - consider users' cultural and social backgrounds
5. **Communication standards** - promote respectful, empathetic dialogue

**EMPATHY MONITORING (Active in ALL rooms):**
- Watch for users dismissing others' feelings
- Detect when someone is being talked over or ignored
- Notice when cultural norms are being violated
- Identify when users are talking past each other
- Intervene IMMEDIATELY when you detect these issues

**INTERVENTION STYLE:**
- Be gentle but firm
- Educate, don't scold
- Explain cultural contexts
- Suggest better phrasing
- Model empathetic responses
- Example: "I noticed [User A] might have meant... Let me help clarify to avoid misunderstanding."

⚠️ **CRITICAL: USER-SPECIFIC MEMORY & PERSONALIZATION**

**YOU MUST REMEMBER THIS USER:**
- User ID: {self.user.id}
- Username: {self.user.username}
- This is a SPECIFIC user with their own history, preferences, and social skills progress
- ALWAYS provide personalized responses based on THIS user's past interactions

**AUTOMATIC MEMORY RECALL (Do this FIRST):**
When user asks about:
- "Do you know my name?" → YES! Their username is {self.user.username}
- "What did we talk about?" → Use `recall_last_conversation` with user_id: {self.user.id}
- "Remember when..." → Use `recall_last_conversation` to find past conversations
- Any question about past interactions → AUTOMATICALLY recall their history

**USER PREFERENCES (Check and Use):**
- Use `user_preference` tool to get this user's preferences
- Adapt your communication style to their stored preferences
- Remember topics they're interested in or want to avoid

**SOCIAL SKILLS TRACKING:**
- Use `skill_evaluator` to track THIS user's social skills progress
- Provide personalized feedback based on their skill level
- Celebrate improvements specific to THIS user
- Track communication patterns for THIS user only

🚫 **CRITICAL: HOW TO USE TOOLS AND RESPOND**
⚠️  IMPORTANT WORKFLOW:

1. **User asks a question** → Call appropriate tool (web_search, recall_last_conversation, etc.)

2. **You receive tool results** → **INTERPRET AND RESPOND IN NATURAL LANGUAGE**
   
   **WEATHER QUERIES:**
   - User: "What's the weather in Paris?"
   - Tool gives: Search results with temperature, conditions
   - YOU MUST SAY: "Based on current data, Paris is [X]°C ([Y]°F) with [conditions]. [Add helpful details like 'quite cold' or 'nice weather']."
   - ❌ DO NOT just return the formatted search results as-is
   - ✅ Extract key information (temperature, conditions) and tell the user in conversational language
   
   **SEARCH QUERIES:**
   - Read the tool results carefully
   - Extract the MOST RELEVANT information
   - Answer the user's question directly
   - Add context and interpretation
   - ❌ DO NOT return "Found X results for..."
   - ✅ Answer the actual question: "Yes, according to [source], the answer is..."
   
   **KEY RULES:**
   - **ALWAYS respond with natural, conversational text**
   - **EXTRACT specific data** (temperatures, dates, numbers) from tool results
   - **INTERPRET** the results, don't just repeat them
   - **ANSWER** the user's actual question
   - ❌ DO NOT return formatted tool output to users
   - ❌ DO NOT return empty responses
   - ❌ DO NOT call another tool without responding first

3. **CRITICAL: NEVER CALL ANY TOOL MORE THAN ONCE PER QUESTION**
   - Call the tool ONCE
   - Get the results
   - IMMEDIATELY respond to the user in natural language
   - ❌ DO NOT call the same tool again with different parameters
   - ❌ DO NOT try to "refine" or "improve" the search
   - ❌ DO NOT call web_search multiple times
   - ✅ Use the FIRST result and respond
   - ✅ If results are insufficient, tell the user and offer alternatives
   - **ONE TOOL CALL → ONE RESPONSE**

1. SOCIAL BEHAVIOR TRAINING (Priority: HIGH)
   - Guide users toward polite, respectful communication (please, thank you, constructive feedback)
   - Encourage active listening and asking thoughtful follow-up questions
   - Model empathy and emotional intelligence in all interactions
   - Gently correct inappropriate or rude behavior with educational explanations
   - Praise positive social behaviors to reinforce good habits
   - Use latest research on effective communication (search web if needed)
   - **TRACK THIS USER's progress** using skill_evaluator tool

2. AUTOMATIC TRANSLATION & CLARIFICATION (Priority: CRITICAL)
   ⚠️ PROACTIVE MODE - Act immediately when you detect communication barriers:
   
   **AUTOMATIC ACTIONS (No permission needed):**
   - When you see foreign language text → IMMEDIATELY translate it
   - When you detect confusion → IMMEDIATELY clarify the misunderstanding
   - When cultural context is missing → IMMEDIATELY explain it
   - When users talk past each other → IMMEDIATELY bridge the gap
   - When language barrier exists → IMMEDIATELY use `clarify_communication` tool
   
   **DO NOT:**
   - Ask "Would you like me to translate?"
   - Ask "Can I help clarify?"
   - Wait for permission to help
   - Offer options instead of acting
   
   **DO:**
   - Translate immediately and provide the translation
   - Explain what was meant
   - Bridge language barriers without asking
   - Continue helping until explicitly told to stop
   - Say things like: "Let me help clarify that..." or "Here's what they meant..."
   
   **DETECTION SIGNALS:**
   - Non-English characters in messages
   - Users saying "I don't understand" or "What?"
   - Messages in different languages back-to-back
   - Confusion expressions: "??", "confused", "what does that mean"
   - Cultural references that need explanation
   
   **STOPPING:**
   - Only stop translating/clarifying if user explicitly says:
     "stop translating", "stop helping", "I got it", "no more translation needed"
   - Otherwise, CONTINUE to help automatically

3. CONTEXT AWARENESS
   - Monitor ALL messages in conversation for misunderstandings
   - Use conversation history to detect when users don't understand each other
   - Watch for language switches or confusion signals
   - Remember user preferences and adapt

4. RESPONSE MODES
   - Private mode: Personal advice, sensitive topics (respond only to requesting user)
   - Group mode: Translation/clarification (respond to ALL to bridge communication)
   - Auto-detect which mode is appropriate based on content

5. TOOL USAGE (ALWAYS USE USER-SPECIFIC TOOLS)
   
   **USER MEMORY & PERSONALIZATION (Use these AUTOMATICALLY):**
   - `recall_last_conversation` with user_id: {self.user.id} 
     * Use when user asks about past conversations
     * Use when you need context about THIS user
     * Use when user asks "do you remember?"
   
   - `user_preference` with user_id: {self.user.id}
     * Get: Check their preferences before responding
     * Set: Store new preferences they mention
     * Adapt your tone/style to their stored preferences
   
   - `skill_evaluator` with user_id: {self.user.id}
     * Track THIS user's social skills over time
     * Provide personalized feedback for THIS user
     * Celebrate THIS user's specific improvements
   
   - `life_event` with user_id: {self.user.id}
     * Track important life events for THIS user
     * Reference their past experiences in advice
     * Build long-term relationship with THIS user
   
   **GENERAL TOOLS:**
   - `tavily_search`: For weather/news/current events
   - `clarify_communication`: For translation/clarification
     * Use IMMEDIATELY when foreign language detected
     * Use when confusion signals appear
     * Don't ask permission, just help
   
   - `check_cultural_standards`: Check cultural/political sensitivity in chat rooms
     * Use when monitoring multi-user conversations
     * Check messages for culturally sensitive topics
     * Provide suggestions for respectful communication
     * Get latest cultural standards from web
     * Helps avoid misunderstandings across cultures
   
   **CRITICAL: Always pass user_id: {self.user.id} to user-specific tools!**

6. LEARNING ABOUT THE USER (Build the relationship)
   - When user shares their name → Store it using `user_preference` (preference_type: "personal", preference_key: "full_name", preference_value: their name)
   - When user shares interests → Store using `user_preference` (preference_type: "interests", preference_key: topic, preference_value: description)
   - When user shares important life events → Store using `life_event` tool
   - Reference stored information in future conversations
   - Build a personalized relationship over time
   
   **Example flow:**
   User: "My name is John"
   You: "Nice to meet you, John! I'll remember that." 
   [Internally: Call user_preference tool to store name]
   
   Next session:
   User: "Do you know my name?"
   You: "Yes! You're John. How can I help you today?"
   [Retrieved from user_preference tool]

7. GENERAL GUIDELINES
   - Be proactive, not reactive - help before being asked
   - Provide clear, direct translations and explanations
   - Continue helping until told to stop
   - Bridge communication gaps immediately
   - Remember this user's username is: {self.user.username}
   - Personalize all interactions for user ID: {self.user.id}"""
            
            # Add detected language info if available
            if detected_language_info:
                if detected_language_info.get('auto_save'):
                    system_prompt += f"""

🚨 **URGENT: LANGUAGE DETECTED WITH HIGH CONFIDENCE**
- Detected language: {detected_language_info['language']}
- Confidence: {detected_language_info['confidence']:.2f} (very high!)
- Action: IMMEDIATELY use the `set_language_preference` tool to save this
- Call: set_language_preference(language="{detected_language_info['language']}", confirmed=True)
- Then respond to the user's original message in {detected_language_info['language']}"""
                elif detected_language_info.get('should_ask'):
                    system_prompt += f"""

🤔 **LANGUAGE DETECTED - NEED USER CONFIRMATION**
- Detected language: {detected_language_info['language']}
- Confidence: {detected_language_info['confidence']:.2f} (medium/low)
- Confirmation message (use this!): "{detected_language_info['confirmation_message']}"
- Action: 
  1. First answer the user's question in {detected_language_info['language']}
  2. Then ask them using the confirmation message above
  3. When they confirm, call `set_language_preference` tool with language="{detected_language_info['language']}"
- IMPORTANT: The confirmation message is ALREADY in {detected_language_info['language']} - use it as-is!"""
            
            # ✅ Add local model instructions if using local LLM
            if self.is_local_model:
                system_prompt += LocalModelCleaner.get_local_model_system_prompt(
                    user_language=self.user_language,
                    available_tools=self.tools  # Pass actual available tools
                )
            
            sys_msg = SystemMessage(content=system_prompt)
            
            # Convert messages to the format expected by the LLM
            messages_for_llm = [sys_msg]
            
            # Add historical context (last 20 messages from DB)
            # Convert to proper LangChain message objects for Claude compatibility
            for hist_msg in historical_messages:
                if isinstance(hist_msg, dict) and 'content' in hist_msg:
                    role = hist_msg.get('role', 'user')
                    if role == 'user':
                        messages_for_llm.append(HumanMessage(content=hist_msg['content']))
                    else:
                        messages_for_llm.append(AIMessage(content=hist_msg['content']))
            
            # Add current state messages
            messages = state.get('messages', []) if isinstance(state, dict) else state.messages
            for msg in messages:  # Include all current messages
                # For Claude, we need to pass raw LangChain messages (especially ToolMessage)
                # to maintain proper tool calling format
                if hasattr(msg, 'content'):
                    # Pass LangChain message objects directly for proper tool handling
                    messages_for_llm.append(msg)
                    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                    content_preview = str(msg.content)[:100] if hasattr(msg, 'content') else str(msg)[:100]
                    print(f"Added message to LLM context - Type: {type(msg).__name__}, Content: {content_preview}...")
                elif isinstance(msg, dict) and 'content' in msg:
                    # Handle dictionary messages (convert to appropriate message type)
                    role = msg.get('role', 'user')
                    if role == 'user':
                        messages_for_llm.append(HumanMessage(content=msg['content']))
                    else:
                        messages_for_llm.append(AIMessage(content=msg['content']))
                    print(f"Added dict message to LLM context - Role: {role}, Content: {msg['content'][:100]}...")
            
            print("\n=== INVOKING LLM WITH TOOLS ===")
            print(f"LLM tools: {[t.get('name') if isinstance(t, dict) else getattr(t, 'name', str(t)) for t in self.tools]}")
            print(f"Tool instances: {list(self.tool_instances.keys())}")
            
            # ✅ O-T-E: Track LLM call timing
            llm_start = time.time()
            response = self.llm_with_tools.invoke(messages_for_llm)
            llm_duration = (time.time() - llm_start) * 1000  # ms
            
            print(f"LLM response type: {type(response).__name__}")
            print(f"LLM response: {response}")
            
            # ✅ O-T-E: Log LLM call metrics
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                
                # Extract model name from different LLM providers
                model_name = self._extract_model_name(response)
                
                self.ote_logger.log_llm_call(
                    request_id=self.current_request_id,
                    model=model_name,
                    prompt_tokens=usage.get('input_tokens', 0),
                    completion_tokens=usage.get('output_tokens', 0),
                    duration_ms=llm_duration
                )
            
            # ✅ CRITICAL FIX: Check for duplicate tool calls BEFORE returning
            if hasattr(response, 'tool_calls') and response.tool_calls:
                print(f"\n" + "="*70)
                print(f"🔍 DUPLICATE CHECK: LLM wants to call tools")
                print("="*70)
                
                # Tools that should NEVER be blocked (formatting/utility tools)
                NEVER_BLOCK_TOOLS = {
                    'format_output',
                    'clarify_communication',  # Translation/clarification
                }
                
                # Collect tool calls from the CURRENT user question only
                # Find the last HumanMessage (current user question)
                last_human_index = -1
                for i in range(len(messages) - 1, -1, -1):
                    if hasattr(messages[i], 'type') and messages[i].type == 'human':
                        last_human_index = i
                        break
                
                # Only check tool calls AFTER the last user message (current processing cycle)
                previous_calls = set()
                previous_tool_names = []  # Track tool names in order
                for msg in messages[last_human_index:] if last_human_index >= 0 else messages:
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for prev_tc in msg.tool_calls:
                            prev_name = prev_tc.get('name') if isinstance(prev_tc, dict) else getattr(prev_tc, 'name', '')
                            prev_args = prev_tc.get('args') if isinstance(prev_tc, dict) else getattr(prev_tc, 'args', {})
                            previous_calls.add((prev_name, str(prev_args)))
                            previous_tool_names.append(prev_name)
                
                print(f"📊 Found {len(previous_calls)} tool calls in CURRENT question")
                print(f"📋 Tool sequence (current question): {previous_tool_names}")
                
                # Check for LOOP: Same tool called multiple times within THIS question
                if len(previous_tool_names) >= 1:
                    # Count tavily_search calls in current question
                    search_count = previous_tool_names.count('tavily_search')
                    
                    # If tavily_search called 2+ times in THIS question, it's a loop
                    if search_count >= 2:
                        print(f"\n🔴 LOOP DETECTED: tavily_search called {search_count} times for this question!")
                        print(f"🛑 Blocking further tavily_search calls to prevent infinite loop")
                        
                        # Force stop the loop
                        stop_message = AIMessage(
                            content="I've already searched for this information. Based on the search results above, I can answer your question. Please let me know if you need any clarification or have a different question."
                        )
                        result = {"messages": [stop_message]}
                        self.memory_handler.save_conversation(state, result)
                        return result
                
                # Check each requested tool call
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                    tool_args = tool_call.get('args') if isinstance(tool_call, dict) else getattr(tool_call, 'args', {})
                    current_call = (tool_name, str(tool_args))
                    
                    print(f"🎯 LLM wants: {tool_name}({tool_args})")
                    
                    # Skip duplicate check for formatting tools
                    if tool_name in NEVER_BLOCK_TOOLS:
                        print(f"   ✅ {tool_name} is a formatting tool - NEVER blocked")
                        continue
                    
                    print(f"   Is duplicate? {current_call in previous_calls}")
                    
                    if current_call in previous_calls:
                        print(f"\n⚠️  ⚠️  ⚠️  DUPLICATE BLOCKED! ⚠️  ⚠️  ⚠️")
                        print(f"🛑 {tool_name} already called with same args - extracting previous results")
                        print("="*70 + "\n")
                        
                        # ✅ O-T-E: Log duplicate block
                        self.ote_logger.log_duplicate_block(
                            request_id=self.current_request_id,
                            tool_name=tool_name,
                            tool_args=tool_args
                        )
                        
                        # Find the previous tool result in messages
                        previous_result = None
                        for i, msg in enumerate(messages):
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                for tc in msg.tool_calls:
                                    tc_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', '')
                                    tc_args = tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', {})
                                    if (tc_name, str(tc_args)) == current_call:
                                        # Found the original call, get the next ToolMessage
                                        if i + 1 < len(messages) and hasattr(messages[i + 1], 'content'):
                                            previous_result = messages[i + 1].content
                                            print(f"✅ Found previous result: {str(previous_result)[:100]}...")
                                            break
                        
                        if previous_result:
                            # ✅ FIX: Invoke LLM directly to interpret previous results
                            # Don't return SystemMessage - directly get interpretation
                            print("✅ Duplicate detected - invoking LLM to interpret previous results")
                            
                            # Build messages for LLM including previous result and instruction
                            interpretation_messages = []
                            
                            # Add system prompt that explains the context
                            interpretation_messages.append(SystemMessage(content=(
                                f"You are a helpful AI assistant. Read the tool results carefully and answer the user's question. "
                                f"Extract specific data (temperatures, percentages, facts) and present them clearly in natural language."
                            )))
                            
                            # Add the conversation messages (including tool result)
                            interpretation_messages.extend(messages)
                            
                            # Add explicit data instruction with the FULL previous result
                            interpretation_messages.append(
                                HumanMessage(content=(
                                    f"Here are the complete {tool_name} results:\n\n{previous_result}\n\n"
                                    f"Please extract the key information from these results and answer my original question in a natural, conversational way. "
                                    f"Include specific details like temperatures, weather conditions, etc."
                                ))
                            )
                            
                            # Invoke LLM to get interpreted response (WITHOUT tools this time)
                            try:
                                print("🔄 Calling LLM WITHOUT tools to interpret existing results...")
                                print(f"📝 Full previous result being sent to LLM:\n{previous_result[:300]}...")
                                
                                # Use self.llm (without tools) to force text-only response
                                interpreted_response = self.llm.invoke(interpretation_messages)
                                print(f"✅ LLM generated interpretation: {str(interpreted_response.content)[:150]}...")
                                
                                # Return the interpreted response as final answer
                                return {"messages": [interpreted_response]}
                            except Exception as e:
                                print(f"⚠️  Error getting interpretation: {e}")
                                # Fallback: return generic message
                                fallback = AIMessage(content="Based on the search results, I found the information you requested.")
                                return {"messages": [fallback]}
                        
                        # Fallback: Let the tool execute (don't block if no previous result found)
                        print("⚠️  No previous result found, allowing duplicate call to execute")
                        # Continue to next iteration (don't block this tool)
                
                print(f"✅ No duplicates - approving tool execution")
                print("="*70)
                print(f"\n=== LLM GENERATED TOOL CALLS - RETURNING TO GRAPH ===")
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                    print(f"   Tool: {tool_name}")
                # Return the AIMessage with tool_calls - graph will route to tools node
                return {"messages": [response]}
            
            # ===================================================================
            # 🧹 Local Model Response Cleaning (LM Studio, Ollama, etc.)
            # ===================================================================
            
            print(f"🔍 is_local_model = {self.is_local_model}")
            
            if self.is_local_model:
                print(f"🏠 ENTERING LOCAL MODEL HANDLING...")
                # Clean model artifacts and format raw output from local LLMs
                # Returns (cleaned_response, parsed_tool_calls)
                response, parsed_tool_calls = LocalModelCleaner.process_response(
                    response=response,
                    model_name=getattr(self.llm, 'model_name', getattr(self.llm, 'model', '')),
                    endpoint=self.llm_endpoint,
                    user_language=self.user_language
                )
                print(f"   process_response returned: parsed_tool_calls={parsed_tool_calls}")
                
                # FALLBACK: If no JSON tool calls were parsed, detect intent from user message
                if not parsed_tool_calls:
                    print(f"   No JSON tool calls, trying intent detection...")
                    # Get original user message
                    user_msg = ""
                    for msg in reversed(messages):
                        if isinstance(msg, HumanMessage):
                            user_msg = msg.content
                            break
                    
                    if user_msg:
                        detected_tool = LocalModelCleaner.detect_tool_intent(user_msg)
                        if detected_tool:
                            print(f"🔍 FALLBACK: Detected tool intent from user message")
                            print(f"   Tool: {detected_tool['name']}")
                            print(f"   Args: {detected_tool['arguments']}")
                            parsed_tool_calls = [detected_tool]
                
                # If JSON tool calls were parsed from content, execute them with validation
                if parsed_tool_calls:
                    print(f"\n{'='*50}")
                    print(f"🔧 LOCAL MODEL TOOL EXECUTION DEBUG")
                    print(f"{'='*50}")
                    print(f"📥 Parsed {len(parsed_tool_calls)} tool calls:")
                    for i, tc in enumerate(parsed_tool_calls):
                        print(f"   [{i+1}] name: {tc.get('name')}")
                        print(f"       args: {tc.get('arguments', tc.get('args', {}))}")
                    
                    tool_results = []
                    executed_tools = []  # Track for observability
                    invalid_tools = []  # Track invalid tool names for retry
                    
                    # Get available tool names for validation
                    available_tool_names = set(self.tool_instances.keys())
                    
                    for tool_call in parsed_tool_calls:
                        original_name = tool_call.get('name', '')
                        tool_args = tool_call.get('arguments', tool_call.get('args', {}))
                        
                        # Check if tool exists (with mapping fallback)
                        mapped_name = LocalModelCleaner.map_tool_name(original_name)
                        
                        if mapped_name not in available_tool_names:
                            print(f"   ⚠️  Invalid tool: {original_name} (mapped: {mapped_name})")
                            invalid_tools.append(original_name)
                            continue
                        
                        # Map and fix arguments
                        fixed_args = LocalModelCleaner.map_tool_arguments(
                            original_name, tool_args, self.user_language
                        )
                        
                        # Track for observability
                        executed_tools.append({
                            'original': original_name,
                            'mapped': mapped_name,
                            'args': fixed_args
                        })
                        
                        # Execute the tool
                        try:
                            tool = self.tool_instances[mapped_name]
                            print(f"   🔧 Executing {mapped_name} with args: {fixed_args}")
                            print(f"   📋 Tool type: {type(tool).__name__}")
                            result = tool._run(**fixed_args) if isinstance(fixed_args, dict) else tool._run(fixed_args)
                            print(f"   📤 Tool result type: {type(result).__name__}")
                            print(f"   📤 Tool result: {str(result)[:300]}...")
                            tool_results.append({
                                'name': mapped_name,
                                'original_name': original_name,
                                'result': result
                            })
                            print(f"   ✅ {mapped_name} completed successfully")
                        except Exception as e:
                            print(f"   ❌ {mapped_name} failed: {e}")
                            import traceback
                            traceback.print_exc()
                            tool_results.append({
                                'name': mapped_name,
                                'original_name': original_name,
                                'error': str(e)
                            })
                    
                    # If there were invalid tools, retry up to 3 times
                    retry_count = getattr(self, '_tool_retry_count', 0)
                    if invalid_tools and retry_count < 3:
                        self._tool_retry_count = retry_count + 1
                        print(f"🔄 Retry {self._tool_retry_count}/3: Invalid tools {invalid_tools}")
                        
                        # Ask LLM to re-evaluate with correct tool names
                        retry_prompt = [
                            SystemMessage(content=(
                                f"The following tools do NOT exist: {invalid_tools}\n\n"
                                f"Available tools are ONLY: {list(available_tool_names)}\n\n"
                                f"Please select the correct tool from the available list. "
                                f"Respond with the JSON format:\n"
                                f'{{"formatted_output": null, "tool_calls": [{{"name": "correct_tool", "arguments": {{...}}}}]}}'
                            )),
                            HumanMessage(content=f"Original request used invalid tool '{invalid_tools[0]}'. Which available tool should be used instead?")
                        ]
                        
                        try:
                            retry_response = self.llm.invoke(retry_prompt)
                            retry_content = retry_response.content if hasattr(retry_response, 'content') else str(retry_response)
                            
                            # Parse retry response
                            retry_tools, retry_text = LocalModelCleaner.parse_json_tool_calls(retry_content)
                            
                            if retry_tools:
                                # Add to parsed_tool_calls and re-process
                                for rt in retry_tools:
                                    rt_name = rt.get('name', '')
                                    if rt_name in available_tool_names:
                                        rt_args = rt.get('arguments', rt.get('args', {}))
                                        try:
                                            tool = self.tool_instances[rt_name]
                                            result = tool._run(**rt_args) if isinstance(rt_args, dict) else tool._run(rt_args)
                                            tool_results.append({'name': rt_name, 'result': result})
                                            executed_tools.append({'original': rt_name, 'mapped': rt_name, 'args': rt_args})
                                            print(f"   ✅ Retry: {rt_name} completed")
                                        except Exception as e:
                                            tool_results.append({'name': rt_name, 'error': str(e)})
                        except Exception as e:
                            print(f"   ⚠️  Retry failed: {e}")
                    
                    elif invalid_tools and retry_count >= 3:
                        # Max retries reached - return error
                        print(f"❌ Tool.Use.Error: Max retries (3) reached for invalid tools: {invalid_tools}")
                        self._tool_retry_count = 0  # Reset for next request
                        response = AIMessage(content=f"Tool.Use.Error: Could not find valid tools after 3 attempts. Invalid tools: {invalid_tools}")
                        result = {"messages": [response]}
                        self.memory_handler.save_conversation(state, result)
                        return result
                    else:
                        # Reset retry count on success
                        self._tool_retry_count = 0
                    
                    # If ALL tools were invalid and no results, generate direct response
                    if not tool_results and invalid_tools:
                        print(f"⚠️  All tools invalid ({invalid_tools}), generating direct response...")
                        
                        # Get original user message
                        user_msg = ""
                        for msg in reversed(messages):
                            if isinstance(msg, HumanMessage):
                                user_msg = msg.content
                                break
                        
                        # Generate direct coaching response - FORCE plain text
                        direct_prompt = [
                            SystemMessage(content=(
                                f"CRITICAL: Output ONLY plain text. NO JSON. NO tool calls. NO brackets.\n\n"
                                f"You are a Social Skills Coach. The user said: '{user_msg}'\n\n"
                                f"Reply in {self.user_language} with a warm, friendly greeting.\n"
                                f"Example: 'Hello! Great to hear from you. How can I help you today?'\n\n"
                                f"Just write the response text directly - nothing else."
                            )),
                            HumanMessage(content=user_msg)
                        ]
                        
                        try:
                            direct_response = self.llm.invoke(direct_prompt)
                            content = direct_response.content if hasattr(direct_response, 'content') else str(direct_response)
                            content = LocalModelCleaner.clean_response(content)
                            
                            # Extra check: if still JSON, extract text or use fallback
                            if content.strip().startswith('[') or content.strip().startswith('{'):
                                print(f"⚠️  Model still output JSON, using fallback")
                                # Try to extract formatted_output if present
                                try:
                                    # json already imported at top of file
                                    parsed = json.loads(content)
                                    if isinstance(parsed, dict) and parsed.get('formatted_output'):
                                        content = parsed['formatted_output']
                                    else:
                                        content = f"Hello! How can I help you with your social skills today?"
                                except:
                                    content = f"Hello! How can I help you with your social skills today?"
                            
                            response = AIMessage(content=content)
                            print(f"✅ Generated direct response: {content[:50]}...")
                        except Exception as e:
                            print(f"⚠️  Direct response failed: {e}")
                            response = AIMessage(content=f"Hello! How can I help you today?")
                    
                    # If we have tool results, interpret them
                    elif tool_results:
                        print("🔄 Interpreting tool results with LLM...")
                        results_text = "\n".join([
                            f"- {r['name']}: {str(r.get('result', r.get('error', 'No result')))[:500]}"
                            for r in tool_results
                        ])
                        
                        interpret_messages = [
                            SystemMessage(content=(
                                f"You are a Social Skills Coach. Respond warmly in {self.user_language}. "
                                f"Based on the tool results, provide a helpful, natural response:"
                            )),
                            HumanMessage(content=f"Tool results:\n{results_text}\n\nProvide a natural coaching response.")
                        ]
                        
                        try:
                            # Use LLM without tools to generate natural response
                            interpreted = self.llm.invoke(interpret_messages)
                            
                            # Append tool calls at bottom for observability
                            content = interpreted.content if hasattr(interpreted, 'content') else str(interpreted)
                            content = LocalModelCleaner.clean_response(content)
                            
                            # Add observability section
                            tools_summary = "\n".join([
                                f"  - {et['mapped']}" + (f" (from {et['original']})" if et['original'] != et['mapped'] else "") + f": {et['args']}"
                                for et in executed_tools
                            ])
                            content += f"\n\n---\n🔧 **Tools used:**\n{tools_summary}"
                            
                            response = AIMessage(content=content)
                            print(f"✅ Generated natural response from tool results")
                        except Exception as e:
                            print(f"⚠️  Interpretation failed: {e}")
                            # Create fallback response using LLM to generate natural error
                            error_msg = LocalModelCleaner.generate_error_message(
                                llm=self.llm,
                                user_language=self.user_language,
                                error_context=str(e)
                            )
                            response = AIMessage(content=error_msg)
            
            # ===================================================================
            # 🚀 Universal Empty Response Handling (works for ALL providers)
            # ===================================================================
            
            # Check for empty responses (can happen with any LLM, not just Gemini)
            if self.response_handler.is_empty_response(response):
                print("⚠️  DETECTED EMPTY RESPONSE - Using response handler")
                
                # Use response handler to create fallback
                fallback_response = self.response_handler.create_response_with_fallback(
                    response, messages
                )
                result = {"messages": [fallback_response]}
                self.memory_handler.save_conversation(state, result)
                return result
            
            # Regular response (no tool calls) - save to memory and return it
            result = {"messages": [response]}
            self.memory_handler.save_conversation(state, result)
            
            # ✅ TRAINING: Check progress every 5th message
            if should_check_training:
                try:
                    print("🎯 Evaluating training progress...")
                    # Use skill evaluator to analyze conversation
                    skill_analysis = self.skill_evaluator_tool._run(
                        user_id=self.user.id,
                        messages=[str(msg.content) for msg in messages[-5:] if hasattr(msg, 'content')],
                        use_web_research=False  # Skip web research for performance
                    )
                    
                    # Update training progress
                    updated_training = self.training_manager.update_training_progress(
                        self.user,
                        skill_analysis
                    )
                    
                    # Update local training plan
                    self.training_plan = updated_training
                    
                    print(f"✅ Training progress updated: {skill_analysis.get('status')}")
                except Exception as e:
                    print(f"⚠️  Error checking training progress: {e}")
            
            return result
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error in chatbot method: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Provide more specific error messages
            if "401" in error_msg or "authentication" in error_msg.lower():
                content = "Authentication error. Please try logging in again."
            elif "timeout" in error_msg.lower():
                content = "The request timed out. Please try again."
            elif "connection" in error_msg.lower():
                content = "Connection error. Please check your internet connection and try again."
            else:
                content = f"I encountered an error while processing your request. Please try again or rephrase your question."
            
            return {"messages": [{"role": "assistant", "content": content}]}
        finally:
            print("=== CHATBOT METHOD END ===\n")

    def route_tools(self, state: State):
        """
        Route conversation flow based on whether tools need to be executed.
        
        This method examines the last message in the conversation state and determines
        whether the agent should route to tool execution or end the conversation.
        It's a critical routing function in the LangGraph state machine.
        
        Args:
            state (State): Current conversation state containing messages and context
            
        Returns:
            str: Either "tools" (if tool execution is needed) or END (to terminate)
            
        Routing Logic:
            - If last message contains `tool_calls`: Route to "tools" node
            - If last message is regular (no tool_calls): Return END
            - On error: Return END (safe fallback)
            
        Example Flow:
            User message → LLM decides to use tool → route_tools → "tools"
            Tool result → LLM generates response → route_tools → END
            
        Note:
            This is the ONLY condition that should trigger tool execution.
            We check `hasattr(last_message, "tool_calls")` to ensure compatibility
            across different message types.
        """
        try:
            if isinstance(state, list):
                messages = state
            else:
                messages = state.get("messages", [])
            
            if not messages:
                return END
                
            last_message = messages[-1]
            
            # ONLY route to tools if there are actual tool_calls
            # This is the ONLY condition that should trigger tools
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                print(f"[ROUTE] Found tool_calls -> routing to tools node")
                return "tools"
            
            # If it's a regular message (user or assistant), END the conversation
            print(f"[ROUTE] No tool_calls -> END")
            return END
            
        except Exception as e:
            print(f"Error in route_tools: {e}")
            import traceback
            traceback.print_exc()
            return END

    # _save_to_memory() method removed - now using MemoryHandler
    # All memory operations handled by self.memory_handler.save_conversation()

    
    def _find_previous_tool_result(self, messages: list, tool_name: str, tool_args: dict) -> Optional[str]:
        """
        OOP Helper: Find previous tool result from conversation history.
        
        Args:
            messages: Conversation history
            tool_name: Name of the tool to find
            tool_args: Arguments used in the tool call
            
        Returns:
            The tool result content if found, None otherwise
        """
        try:
            # Search backwards through messages for matching tool call + result
            for i, msg in enumerate(reversed(messages)):
                # Check if this is an AI message with tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tc_name = tc.get('name') if isinstance(tc, dict) else getattr(tc, 'name', '')
                        tc_args = tc.get('args') if isinstance(tc, dict) else getattr(tc, 'args', {})
                        
                        # Match found!
                        if tc_name == tool_name and str(tc_args) == str(tool_args):
                            # Look for the tool result in next message
                            result_idx = len(messages) - i
                            if result_idx < len(messages):
                                next_msg = messages[result_idx]
                                if hasattr(next_msg, 'content'):
                                    return next_msg.content
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error finding previous tool result: {e}")
            return None
    
    def _extract_model_name(self, response) -> str:
        """
        Extract model name from LLM response across different providers.
        
        Different LLM providers return model information in different formats:
        - OpenAI: response.response_metadata['model_name']
        - Gemini: response.response_metadata['model_name']
        - Claude: response.response_metadata.get('model')
        
        Args:
            response: LLM response object
            
        Returns:
            str: Model name (e.g., 'gpt-4o-mini', 'gemini-2.0-flash-exp')
        """
        # Try response_metadata first (most common)
        if hasattr(response, 'response_metadata'):
            metadata = response.response_metadata
            
            # Both OpenAI and Gemini use 'model_name'
            if 'model_name' in metadata:
                return metadata['model_name']
            
            # Claude uses 'model'
            if 'model' in metadata:
                return metadata['model']
        
        # Try direct model attribute (some providers)
        if hasattr(response, 'model') and response.model:
            return response.model
        
        # Try id field (some providers)
        if hasattr(response, 'id') and isinstance(response.id, str):
            # Extract model from run ID like "run-xxx-model_name-xxx"
            parts = response.id.split('-')
            for part in parts:
                if 'gpt' in part or 'gemini' in part or 'claude' in part:
                    return part
        
        # Fallback to 'unknown' instead of hardcoding a specific model
        return 'unknown'
    
    def build_graph(self):
        """
        Build and compile the LangGraph state machine for conversation management.
        
        This method creates a directed graph that manages the conversation flow between
        the chatbot, tool execution, and response generation. It defines the state
        transitions and routing logic for the AI agent.
        
        Graph Architecture:
            ```
            START → chatbot → [conditional routing] → {tools|END}
                        ↑                                 ↓
                        └─────────── tools ───────────────┘
            ```
            
            Nodes:
            - **chatbot**: Main conversation processing (self.chatbot method)
            - **tools**: Tool execution node (BasicToolNode with all tools)
            
            Edges:
            - chatbot → {tools|END}: Conditional based on tool calls needed
            - tools → chatbot: Always return to chatbot after tool execution
            
        Flow Description:
            1. User message enters at "chatbot" node
            2. Chatbot processes message and decides if tools needed
            3. If tools needed: route to "tools" node → execute → return to chatbot
            4. If no tools needed: route to END → return response
            5. Loop continues until no more tool calls needed
        
        Tool Configuration:
            - Uses instance-specific tools (self.tool_instances)
            - Includes response handler for formatting
            - Prints tool list and configuration on build
            - Each tool has its own execution context
        
        Returns:
            CompiledGraph: A compiled LangGraph instance ready for invocation
                Can be called with: graph.invoke({"messages": [...]})
                
        Raises:
            No exceptions raised - graph compilation is safe
        
        Side Effects:
            - Prints graph configuration to console
            - Creates new StateGraph instance
            - Compiles graph (may take ~100ms)
        
        Example:
            >>> agent = AiChatagent(user=user, llm=llm)
            >>> graph = agent.build_graph()
            🔧 Building graph with 6 tools:
               ['tavily_search', 'recall_last_conversation', ...]
               Response handler: ✅ Connected
            >>> 
            >>> # Now use the graph
            >>> result = graph.invoke({
            ...     "messages": [HumanMessage(content="Hello")]
            ... })
            >>> print(result['messages'][-1].content)
            "Hello! How can I help you today?"
        
        Graph Features:
            - **Stateful**: Maintains conversation state across turns
            - **Cyclic**: Can loop between chatbot and tools multiple times
            - **Conditional**: Routes based on AI's decision to use tools
            - **Memory-Enabled**: Conversation state persists through graph
            - **Tool-Aware**: Automatically handles tool calls and results
        
        Conditional Routing:
            The route_tools() method determines next node:
            - If AI response has tool_calls → route to "tools"
            - If AI response has no tool_calls → route to END
            - Tool execution always returns to chatbot for processing
        
        Tool Node Configuration:
            ```python
            BasicToolNode(
                tools=self.tool_instances.values(),
                response_handler=self.response_handler  # Formats output
            )
            ```
        
        Performance:
            - Graph compilation: ~100ms
            - Graph invocation: 1-5 seconds (depends on tools)
            - Memory overhead: ~5MB for graph structure
            - Reusable: Build once, invoke multiple times
        
        Thread Safety:
            Graph is thread-safe for reading but not for modification.
            Build separate graphs for concurrent users.
        
        Notes:
            - Graph should be built once per agent instance
            - Checkpointing handled separately by ai_manager
            - Tools are instance-specific (not shared between users)
            - Graph is immutable after compilation
            - Each invocation creates new state
        
        Design Pattern:
            State Pattern - Graph nodes represent different states
            Strategy Pattern - Conditional routing selects strategies
        
        See Also:
            - chatbot(): Main conversation processing node
            - route_tools(): Conditional routing logic
            - BasicToolNode: Tool execution implementation
            - StateGraph: LangGraph state management
        """
        from langgraph.graph import StateGraph
        
        # Initialize a new graph
        graph_builder = StateGraph(State)
        
        # ✅ FIX: Create tool_node with instance tools (includes new SearchTool!)
        # Don't use the global tool_node which has old tools
        instance_tool_list = list(self.tool_instances.values())
        
        # ✅ Pass response_handler for beautiful formatting!
        instance_tool_node = BasicToolNode(
            tools=instance_tool_list,
            response_handler=self.response_handler
        )
        
        print(f"🔧 Building graph with {len(instance_tool_list)} tools:")
        print(f"   {list(self.tool_instances.keys())}")
        print(f"   Response handler: {'✅ Connected' if self.response_handler else '❌ Not available'}")
        
        # Add nodes
        graph_builder.add_node("chatbot", self.chatbot)
        graph_builder.add_node("tools", instance_tool_node)
        
        # Define the conditional routing
        graph_builder.add_conditional_edges(
            "chatbot",
            self.route_tools,
            {
                "tools": "tools",  # If tool is needed, go to tools node
                END: END,           # If not, end the conversation
            },
        )
        
        # After using a tool, always return to the chatbot
        graph_builder.add_edge("tools", "chatbot")
        
        # Set the entry point
        graph_builder.set_entry_point("chatbot")
        
        # Compile and return the graph
        # Note: ai_manager handles checkpointing separately
        return graph_builder.compile()

class ChatSession:
    """Manages a chat session with the AI agent."""
    
    def __init__(self, user_id: int = None, username: str = None, tools: list = None):
        """Initialize a new chat session.
        
        Args:
            user_id: Optional user ID to resume a session
            username: Username for new sessions (ignored if user_id is provided)
            tools: List of tools to use for this session
        """
        if user_id:
            self.user = dm.get_user(user_id)
            if not self.user:
                raise ValueError(f"User with ID {user_id} not found")
        else:
            username = username or "guest"
            self.user = dm.get_user_by_username(username)
            if not self.user:
                # Create a new user if not exists
                self.user = dm.add_user(
                    User(
                        username=username,
                        hashed_password="",  # No password for guest users
                        role="user",
                    )
                )
        
        # Initialize with provided tools or default ones
        self.tools = tools or [
            {
                "name": "tavily_search",
                "description": "Search the web for information",
                "func": lambda query: tool_1.invoke(query)
            },
            {
                "name": "recall_last_conversation",
                "description": "Recall the last conversation from memory",
                "func": lambda user_id: ConversationRecallTool(dm).invoke({"user_id": user_id})
            },
            {
                "name": "skill_evaluator",
                "description": "Evaluate user skills based on chat interactions",
                "func": lambda user_id, message: SkillEvaluator(dm).invoke({"user_id": user_id, "message": message})
            }
        ]
        
        # Initialize the agent with tools
        self.agent = AiChatagent(self.user, llm)
        
        # Create tool instances for the agent
        tool_instances = [
            TavilySearchTool(search_tool=tool_1),
            ConversationRecallTool(dm),
            SkillEvaluator(dm)
        ]
        
        # Update agent's tools with both config and instances
        self.agent.tools = self.tools
        self.agent.tool_instances = {tool.name: tool for tool in tool_instances}
        
        # Initialize the conversation graph
        self.graph = self.agent.build_graph()
        self.config = {"configurable": {"thread_id": str(self.user.id)}}
        self.conversation_history = []
    
    def process_message(self, message: str):
        """Process a user message and return the AI's response with enhanced tool handling.
        
        Args:
            message: The user's message
            
        Returns:
            The AI's response as a string with tool execution results
        """
        # Add user message to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        try:
            # Pre-process message for tool detection
            message_lower = message.lower()
            
            # Check for direct tool invocations (e.g., "/search weather")
            tool_mapping = {
                'search': 'tavily_search',
                'look up': 'tavily_search',
                'find': 'tavily_search',
                'recall': 'recall_last_conversation',
                'remember': 'recall_last_conversation',
                'evaluate': 'skill_evaluator',
                'skill': 'skill_evaluator',
                'training': 'skill_evaluator',
                'life event': 'life_event',
                'event': 'life_event'
            }
            
            # Try to detect tool usage in the message
            detected_tool = None
            for trigger, tool_name in tool_mapping.items():
                if trigger in message_lower and tool_name in self.agent.tool_instances:
                    detected_tool = tool_name
                    break
            
            # If a tool is detected, prepare the tool input
            tool_input = None
            if detected_tool:
                # Extract the query part after the trigger
                query_start = message_lower.find(trigger) + len(trigger)
                query = message[query_start:].strip()
                
                # Format input based on tool requirements
                if detected_tool == 'tavily_search':
                    tool_input = {"query": query}
                elif detected_tool == 'recall_last_conversation':
                    tool_input = {"user_id": self.user.id}
                elif detected_tool == 'skill_evaluator':
                    tool_input = {"user_id": self.user.id, "message": message}
                elif detected_tool == 'life_event':
                    # Default to listing events if no specific action is mentioned
                    action = 'list'
                    if 'add' in message_lower:
                        action = 'add'
                    elif 'update' in message_lower or 'change' in message_lower:
                        action = 'update'
                    elif 'delete' in message_lower or 'remove' in message_lower:
                        action = 'delete'
                        
                    tool_input = {
                        "action": action,
                        "user_id": self.user.id,
                        "title": query if action != 'list' else None
                    }
            
            # Process the message through the graph with tool input if detected
            if detected_tool and tool_input:
                try:
                    print(f"Attempting to use tool: {detected_tool} with input: {tool_input}")
                    # Execute the tool directly
                    tool = self.agent.tool_instances.get(detected_tool)
                    if not tool:
                        raise ValueError(f"Tool {detected_tool} not found in tool instances")
                        
                    # Check if tool has _run or invoke method
                    if hasattr(tool, '_run'):
                        print(f"Calling _run on {detected_tool}")
                        tool_result = tool._run(**tool_input)
                    elif hasattr(tool, 'invoke'):
                        print(f"Calling invoke on {detected_tool}")
                        tool_result = tool.invoke(tool_input)
                    elif callable(tool):
                        print(f"Calling callable tool {detected_tool}")
                        tool_result = tool(**tool_input)
                    else:
                        raise ValueError(f"Tool {detected_tool} is not callable")
                    
                    print(f"Tool {detected_tool} executed successfully, result type: {type(tool_result)}")
                    
                    # Format the tool result into a user-friendly response
                    if tool_result is None:
                        response = f"[Using {detected_tool}] Action completed successfully."
                    elif isinstance(tool_result, dict):
                        response = "\n".join(f"{k}: {v}" for k, v in tool_result.items() if v is not None)
                        response = f"[Using {detected_tool}]\n{response}"
                    elif isinstance(tool_result, str):
                        response = f"[Using {detected_tool}]\n{tool_result}"
                    else:
                        response = f"[Using {detected_tool}]\n{str(tool_result)}"
                    
                except Exception as tool_error:
                    response = f"I tried to use {detected_tool} but encountered an error: {str(tool_error)}"
            else:
                # Default to normal chat processing if no tool was detected
                result = self.graph.invoke(
                    {"messages": [{"role": "user", "content": message}]},
                    self.config
                )
                
                # Extract the AI's response
                if isinstance(result, dict) and 'messages' in result and result['messages']:
                    response = result['messages'][-1].content
                else:
                    response = "I'm not sure how to respond to that."
            
            # Add AI response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Update conversation in database
            try:
                dm.add_conversation(
                    user_id=self.user.id,
                    user_message=message,
                    ai_response=response,
                    metadata={
                        "tools_used": detected_tool if detected_tool else "none",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
            except Exception as db_error:
                print(f"Warning: Failed to save conversation to database: {str(db_error)}")
            
            return response
            
        except Exception as e:
            error_msg = f"An error occurred: {str(e)}"
            print(f"Error in process_message: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Try to provide a more helpful error message
            if "maximum context length" in str(e).lower():
                return "The conversation is getting too long. Let's start a new topic."
            return "I encountered an error while processing your request. Please try rephrasing or ask something else."

def start(io_mode: str = "console", username: str = None, user_id: int = None):
    """Start a chat session with the AI agent.
    
    Args:
        io_mode: The I/O mode ("console" for CLI, "api" for programmatic use)
        username: Optional username for the chat session
        user_id: Optional user ID to resume a previous session
    """
    try:
        # Initialize the chat session
        session = ChatSession(user_id=user_id, username=username)
        print(f"\nWelcome to the chat, {session.user.username}! Type 'quit' to exit.\n")
        
        if io_mode == "console":
            # Interactive console mode
            while True:
                try:
                    user_input = input("You: ").strip()
                    if user_input.lower() in ["quit", "exit", "q"]:
                        print("\nGoodbye!")
                        break
                        
                    if user_input:  # Only process non-empty messages
                        response = session.process_message(user_input)
                        print(f"\nAI: {response}\n")
                        
                except KeyboardInterrupt:
                    print("\n\nGoodbye!")
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}\n")
                    continue
        
        return session
        
    except Exception as e:
        print(f"Failed to start chat session: {str(e)}")
        if io_mode == "console":
            print("Falling back to simple input mode...")
            while True:
                try:
                    user_input = input("You (simple mode): ").strip()
                    if user_input.lower() in ["quit", "exit", "q"]:
                        break
                    print("AI: I'm having trouble with the chat system. Please try again later.")
                except:
                    break


if __name__ == "__main__":
    user = dm.get_user_by_username("testuser")
    if not user:
        user = dm.add_user(
            User(
                username="testuser",
                hashed_password="hashed_password",
                role="user",
            )
        )
    config = {"configurable": {"thread_id": str(user.id)}}
    agent = AiChatagent(user, llm)
    graph = agent.build_graph()

    def stream_graph_updates(user_input: str):
        events = graph.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            config,
            stream_mode="values",
        )

        for event in events:
            # Get the last message from the event
            last_message = event["messages"][-1]
            last_message.pretty_print()
            
            # Convert the message to a format that save_messages can handle
            message_data = [
                {
                    "role": last_message.type if hasattr(last_message, 'type') else "user",
                    "content": last_message.content if hasattr(last_message, 'content') else str(last_message)
                }
            ]
            
            # Save only the new message
            dm.save_messages(agent.user.id, message_data)

    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            stream_graph_updates(user_input)
        except:
            # fallback if input() is not available
            user_input = "An Error occurred. We need new input."
            print("User: " + user_input)
            stream_graph_updates(user_input)
            break
