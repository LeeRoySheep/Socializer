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

# Initialize the database manager
db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')
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

from langchain.tools import BaseTool
from pydantic import BaseModel, Field, field_validator
from typing import Type


# ConversationRecallTool has been extracted to tools/conversation_recall_tool.py


class UserPreferenceInput(BaseModel):
    """Input schema for UserPreferenceTool - Gemini compatible."""
    action: str = Field(description="Action to perform: get, set, or delete")
    user_id: int = Field(description="The ID of the user")
    preference_type: Optional[str] = Field(default=None, description="Category of preference")
    preference_key: Optional[str] = Field(default=None, description="Specific preference key")
    preference_value: Optional[str] = Field(default=None, description="Value to set")
    confidence: Optional[float] = Field(default=None, description="Confidence score 0-1")

class UserPreferenceTool(BaseTool):
    """Tool for managing user preferences with encryption for sensitive data."""
    
    name: str = "user_preference"
    description: str = (
        "Manage user preferences (ENCRYPTED). "
        "Use this tool to get, set, or delete user preferences. "
        "Personal data (name, DOB, sensitive info) is automatically encrypted."
    )
    args_schema: Type[BaseModel] = UserPreferenceInput
    dm: DataManager = None
    encryptor: Optional[Any] = None  # Properly declare for Pydantic
    
    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.dm = data_manager
        
        # Initialize encryption for sensitive data
        try:
            from app.security.encryption import get_encryptor
            self.encryptor = get_encryptor()
        except ImportError:
            print("⚠️  WARNING: Encryption module not available, data will be stored unencrypted!")
            self.encryptor = None
        except Exception as e:
            print(f"⚠️  WARNING: Could not initialize encryption: {e}")
            self.encryptor = None
    
    def _run(self, *args, **kwargs) -> dict:
        """Execute the preference tool.
        
        Args:
            action: The action to perform (get/set/delete)
            user_id: The ID of the user
            preference_type: The type/category of preference (required for set/delete)
            preference_key: The specific preference key (required for set/delete)
            preference_value: The value to set (required for set)
            confidence: Confidence score (0-1) for the preference (optional for set)
            
        Returns:
            Dictionary with the result of the operation
        """
        # Handle both direct kwargs and input dict
        if not kwargs and args and isinstance(args[0], dict):
            kwargs = args[0]
            
        action = kwargs.get("action", "").lower()
        user_id = kwargs.get("user_id")
        
        if not user_id:
            return {"status": "error", "message": "user_id is required"}
        
        try:
            if action == "get":
                preference_type = kwargs.get("preference_type")
                preferences_dict = self.dm.get_user_preferences(user_id, preference_type)
                
                # ✅ DECRYPT sensitive preferences before returning
                # preferences_dict format: {"type.key": "value"}
                decrypted_prefs = []
                
                if preferences_dict:
                    for full_key, value in preferences_dict.items():
                        # Split "personal_info.favorite_color" -> ["personal_info", "favorite_color"]
                        if '.' in full_key:
                            pref_type, pref_key = full_key.split('.', 1)
                        else:
                            pref_type = "general"
                            pref_key = full_key
                        
                        # Decrypt if it's sensitive data and encrypted
                        decrypted_value = value
                        is_encrypted = False
                        
                        if self.encryptor and self._is_sensitive_type(pref_type):
                            if value and self.encryptor.is_encrypted(value):
                                try:
                                    decrypted_value = self.encryptor.decrypt(value)
                                    is_encrypted = True
                                except Exception as e:
                                    print(f"Decryption error for {full_key}: {e}")
                        
                        decrypted_prefs.append({
                            "preference_type": pref_type,
                            "preference_key": pref_key,
                            "preference_value": decrypted_value,
                            "encrypted": is_encrypted
                        })
                
                return {
                    "status": "success",
                    "preferences": decrypted_prefs,
                    "total": len(decrypted_prefs),
                    "encryption_enabled": bool(self.encryptor)
                }
                
            elif action == "set":
                required = ["preference_type", "preference_key", "preference_value"]
                if not all(k in kwargs for k in required):
                    return {
                        "status": "error",
                        "message": f"Missing required fields. Required: {', '.join(required)}"
                    }
                
                # ✅ ENCRYPT sensitive data before storing
                preference_value = kwargs["preference_value"]
                preference_type = kwargs["preference_type"]
                
                if self.encryptor and self._is_sensitive_type(preference_type):
                    try:
                        preference_value = self.encryptor.encrypt(preference_value)
                    except Exception as e:
                        return {
                            "status": "error",
                            "message": f"Encryption failed: {str(e)}"
                        }
                
                success = self.dm.set_user_preference(
                    user_id=user_id,
                    preference_type=preference_type,
                    preference_key=kwargs["preference_key"],
                    preference_value=preference_value,
                    confidence=kwargs.get("confidence", 1.0)
                )
                
                if success:
                    return {
                        "status": "success",
                        "message": "Preference set successfully (encrypted)" if self.encryptor and self._is_sensitive_type(preference_type) else "Preference set successfully",
                        "encrypted": bool(self.encryptor and self._is_sensitive_type(preference_type))
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to set preference"
                    }
                    
            elif action == "delete":
                preference_type = kwargs.get("preference_type")
                preference_key = kwargs.get("preference_key")
                
                if not preference_type and not preference_key:
                    return {
                        "status": "error",
                        "message": "Must provide at least one of preference_type or preference_key"
                    }
                
                success = self.dm.delete_user_preference(
                    user_id=user_id,
                    preference_type=preference_type,
                    preference_key=preference_key
                )
                
                if success:
                    return {
                        "status": "success",
                        "message": "Preferences deleted successfully"
                    }
                else:
                    return {
                        "status": "error",
                        "message": "No matching preferences found to delete"
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Invalid action: {action}. Must be one of: get, set, delete"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error in UserPreferenceTool: {str(e)}"
            }
    
    def _is_sensitive_type(self, preference_type: str) -> bool:
        """
        Determine if a preference type contains sensitive data that should be encrypted.
        
        Args:
            preference_type: The type of preference
            
        Returns:
            bool: True if sensitive data requiring encryption
        """
        sensitive_types = {
            'personal_info',    # Name, DOB, address, etc.
            'contact',          # Email, phone, etc.
            'financial',        # Payment info
            'medical',          # Health data
            'identification',   # ID numbers, SSN, etc.
            'private'           # Explicitly private data
        }
        return preference_type.lower() in sensitive_types
    
    async def _arun(self, *args, **kwargs):
        """Async version of run."""
        return self._run(*args, **kwargs)


class SkillEvaluatorInput(BaseModel):
    """Input schema for SkillEvaluator - Gemini compatible."""
    user_id: int = Field(description="The ID of the user to evaluate")
    message: Optional[str] = Field(default=None, description="Single message to evaluate")
    messages: Optional[List[str]] = Field(default=None, description="List of messages to evaluate")
    cultural_context: Optional[str] = Field(default="Western", description="User's cultural background")
    use_web_research: Optional[bool] = Field(default=True, description="Whether to fetch latest research")

class SkillEvaluator(BaseTool):
    """Evaluates user skills based on chat interactions and manages training."""

    name: str = "skill_evaluator"
    description: str = (
        "Evaluate user skills based on chat interactions and manage training. "
        "Analyzes messages for active listening, empathy, clarity, and engagement."
    )
    args_schema: Type[BaseModel] = SkillEvaluatorInput
    dm: DataManager = None
    orchestrator: Optional[SkillEvaluationOrchestrator] = None
    skills: Dict[str, Dict[str, Any]] = {}

    def __init__(self, data_manager: DataManager):
        super().__init__()
        self.dm = data_manager
        self.orchestrator = get_evaluation_orchestrator(data_manager)
        atexit.register(self.cleanup)

        # Define skills for training purposes
        self.skills = {
            "active_listening": {
                "description": "Ability to actively listen and respond appropriately",
                "keywords": ["i understand", "i hear you", "that makes sense"],
            },
            "empathy": {
                "description": "Ability to show understanding and share feelings",
                "keywords": ["i understand how you feel", "that must be"],
            },
            "clarity": {
                "description": "Clear and concise communication",
                "keywords": ["let me explain", "to clarify"],
            },
            "engagement": {
                "description": "Keeping the conversation engaging",
                "keywords": ["what do you think", "how about you"],
            },
        }

    def cleanup(self, user_id: int = None):
        """Clean up resources when the evaluator is destroyed.
        
        Args:
            user_id: Optional user ID to generate skill suggestions for
        """
        if self.orchestrator:
            try:
                if user_id is not None:
                    suggestions = self.get_skill_suggestions(user_id)
                    if suggestions:
                        print("\nSkill Suggestions:")
                        for suggestion in suggestions:
                            print(f"- {suggestion['skill_name']}: {suggestion['suggestion']}")
            except Exception as e:
                print(f"Error generating skill suggestions: {e}")
                
            stop_evaluation_orchestrator()

    def _run(self, *args, **kwargs) -> Dict[str, Any]:
        """Run the skill evaluator tool using the multi-agent system with web research.

        Args:
            user_id: The ID of the user to evaluate
            message: The message to evaluate for skills (optional if messages is provided)
            messages: List of messages to evaluate (optional if message is provided)
            cultural_context: User's cultural background (optional)
            use_web_research: Whether to fetch latest empathy research (default: True)

        Returns:
            Dict containing skill scores, suggestions, and latest research
        """
        try:
            # Handle both direct kwargs and nested input dict
            if not kwargs and len(args) == 1 and isinstance(args[0], dict):
                kwargs = args[0]
                
            user_id = kwargs.get('user_id')
            message = kwargs.get('message')
            messages = kwargs.get('messages', [message] if message else [])
            cultural_context = kwargs.get('cultural_context', 'Western')
            use_web_research = kwargs.get('use_web_research', True)
            
            if not user_id:
                return {"status": "error", "message": "User ID is required"}
                
            if not messages:
                return {"status": "error", "message": "No message or messages provided"}
            
            # ✅ NEW: Get latest empathy research from web
            latest_standards = None
            if use_web_research:
                try:
                    # Search for latest empathy and social skills research
                    research_query = f"latest {cultural_context} empathy social skills research 2024 2025"
                    research_result = tool_1.invoke(research_query)
                    latest_standards = {
                        "query": research_query,
                        "research": str(research_result)[:500],  # Limit to 500 chars
                        "updated": "2025-10-15"
                    }
                except Exception as e:
                    print(f"Web research failed: {e}")
            
            # Get current skill levels
            current_skills = self.get_skill_suggestions(user_id)
            
            # Analyze message for skill demonstration
            analysis = self._analyze_message_skills(message if isinstance(message, str) else str(messages), cultural_context)
            
            return {
                "status": "success",
                "message": "Skill evaluation completed with latest research",
                "current_skills": current_skills,
                "message_analysis": analysis,
                "latest_standards": latest_standards,
                "cultural_context": cultural_context
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"An error occurred while evaluating skills: {str(e)}",
                "current_skills": self.get_skill_suggestions(user_id) if 'user_id' in locals() else []
            }
    
    def _analyze_message_skills(self, message: str, cultural_context: str = "Western") -> Dict[str, Any]:
        """Analyze a message for social skill demonstration.
        
        Args:
            message: The message to analyze
            cultural_context: Cultural context for evaluation
            
        Returns:
            Analysis results with detected skills
        """
        message_lower = message.lower()
        detected_skills = []
        
        for skill_name, data in self.skills.items():
            keywords = data.get('keywords', [])
            if any(keyword.lower() in message_lower for keyword in keywords):
                detected_skills.append({
                    "skill": skill_name,
                    "detected": True,
                    "keywords_found": [kw for kw in keywords if kw.lower() in message_lower]
                })
        
        return {
            "message_length": len(message),
            "detected_skills": detected_skills,
            "skill_count": len(detected_skills),
            "cultural_context": cultural_context,
            "needs_improvement": len(detected_skills) < 2  # Less than 2 skills detected
        }
    
    def get_skill_suggestions(self, user_id: int) -> List[Dict[str, Any]]:
        """Get the current skills and suggestions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of dictionaries containing skill information and suggestions
        """
        suggestions = []
        try:
            for skill_name, data in self.skills.items():
                skill = self.dm.get_or_create_skill(skill_name)
                if not skill:
                    continue
                    
                level = self.dm.get_skilllevel_for_user(user_id, skill.id)
                if level is None:
                    level = 0
                    
                # Always include all skills with their current levels
                suggestion = {
                    "skill": skill_name,
                    "current_level": level,
                    "max_level": 10,  # Maximum possible skill level
                    "description": data.get("description", "No description available"),
                    "suggestion": f"Try using phrases like: {', '.join(data.get('keywords', ['practice more']))[:2]}..." if data.get('keywords') else "Keep practicing to improve this skill",
                    "needs_improvement": level < 7  # Flag for skills that need work
                }
                
                # Add specific feedback based on skill level
                if level >= 8:
                    suggestion["feedback"] = "Excellent! You've mastered this skill."
                elif level >= 5:
                    suggestion["feedback"] = "Good progress! Keep it up!"
                else:
                    suggestion["feedback"] = "Let's work on improving this skill."
                
                suggestions.append(suggestion)
                
            # Sort suggestions by level (lowest first)
            suggestions.sort(key=lambda x: x["current_level"])
            
        except Exception as e:
            print(f"Error generating skill suggestions: {e}")
            # Return a basic response if there's an error
            return [{
                "status": "error",
                "message": "Could not retrieve skill information. Please try again later."
            }]
            
        return suggestions


class TavilySearchInput(BaseModel):
    """Input schema for TavilySearchTool - Gemini compatible."""
    query: str = Field(description="The search query string")

class TavilySearchTool(BaseTool):
    name: str = "tavily_search"
    description: str = """Search the web for current information.
    
    Use this tool when you need to find up-to-date information, current events, 
    or real-time data like time, weather, news, etc.
    
    Input: A search query string (e.g. 'current weather in Paris', 'latest news')
    """
    args_schema: Type[BaseModel] = TavilySearchInput
    search_tool: Any = None  # This needs to be a class variable for Pydantic
    
    def __init__(self, search_tool, **data):
        # Initialize the BaseTool first
        super().__init__(**data)
        # Then set the search tool
        object.__setattr__(self, 'search_tool', search_tool)
    
    def _run(self, query: str, **kwargs):
        """Execute the search tool synchronously."""
        return self._execute_search(query)
    
    async def _arun(self, query: str, **kwargs):
        """Execute the search tool asynchronously."""
        return self._execute_search(query)
    
    def _execute_search(self, query):
        """Execute search and return formatted results."""
        try:
            print(f"Executing search with query: {query}")
            if not query:
                return "No search query provided."
                
            # Handle both string and dict queries
            search_query = query.get('query', '') if isinstance(query, dict) else str(query)
            if not search_query.strip():
                return "Empty search query provided."
                
            # Execute the search
            print(f"Searching for: {search_query}")
            result = self.search_tool.invoke(search_query)
            
            # Handle different result formats
            if not result:
                return "No results found."
                
            if isinstance(result, str):
                return result[:2000]  # Limit length
                
            if isinstance(result, dict):
                # Handle weather API response
                if 'current' in result and 'condition' in result['current']:
                    weather = result['current']
                    location = result.get('location', {})
                    return (
                        f"Current weather in {location.get('name', 'the location')}:\n"
                        f"- Condition: {weather['condition']['text']}\n"
                        f"- Temperature: {weather.get('temp_c', 'N/A')}°C ({weather.get('temp_f', 'N/A')}°F)\n"
                        f"- Feels like: {weather.get('feelslike_c', 'N/A')}°C ({weather.get('feelslike_f', 'N/A')}°F)\n"
                        f"- Wind: {weather.get('wind_kph', 'N/A')} km/h ({weather.get('wind_mph', 'N/A')} mph) {weather.get('wind_dir', '')}\n"
                        f"- Humidity: {weather.get('humidity', 'N/A')}%"
                    )
                
                # Handle Tavily search results
                if 'results' in result and result['results']:
                    # Return the first result's content or description
                    top_result = result['results'][0]
                    return top_result.get('content') or top_result.get('description', 'No content available')
                
                # Fallback to string representation
                return str(result)[:2000]
                
            return str(result)[:2000]  # Limit length of any other type
            
        except Exception as e:
            error_msg = f"Error in Tavily search: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return f"I encountered an error while searching: {str(e)}"
    
    def invoke(self, input_data):
        """Handle tool invocation with flexible input format."""
        print(f"TavilySearchTool invoked with input: {input_data}")
        try:
            if isinstance(input_data, dict) and 'query' in input_data:
                return self._execute_search(input_data['query'])
            elif isinstance(input_data, str):
                return self._execute_search(input_data)
            else:
                return "Error: Invalid input format. Please provide a search query or a dictionary with a 'query' key."
        except Exception as e:
            return {"error": f"Error performing search: {str(e)}"}

# Import the database URL from config
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from app.config import SQLALCHEMY_DATABASE_URL
from datamanager.data_manager import DataManager

# Extract the database path from the URL
db_path = SQLALCHEMY_DATABASE_URL.replace('sqlite:///', '')

# Initialize tools and evaluator with the same database as the main app
dm = DataManager(db_path)
conversation_recall = ConversationRecallTool(dm)
skill_evaluator = SkillEvaluator(dm)
user_preference_tool = UserPreferenceTool(dm)
tavily_search_tool = TavilySearchTool(tool_1)

from datetime import datetime, date
import json
import os
from typing import Dict, List, Any, Optional, Type, Union

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage, HumanMessage

class LifeEventInput(BaseModel):
    """Input model for life event operations - Gemini compatible."""
    action: str = Field(description="Action to perform: add, get, update, delete, list, timeline")
    user_id: int = Field(description="ID of the user")
    event_id: Optional[int] = Field(default=None, description="ID of the event")
    event_type: Optional[str] = Field(default=None, description="Type of the event")
    title: Optional[str] = Field(default=None, description="Title of the event")
    description: Optional[str] = Field(default=None, description="Detailed description")
    start_date: Optional[str] = Field(default=None, description="When event started YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="When event ended YYYY-MM-DD")
    location: Optional[str] = Field(default=None, description="Where event occurred")
    impact_level: Optional[int] = Field(default=None, description="Importance level 1-10")
    is_private: Optional[bool] = Field(default=True, description="Whether event is private")
    limit: Optional[int] = Field(default=50, description="Maximum events to return")
    offset: Optional[int] = Field(default=0, description="Offset for pagination")

    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_dates(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v)
            except (ValueError, TypeError):
                try:
                    return datetime.strptime(v, '%Y-%m-%d')
                except (ValueError, TypeError):
                    pass
        return v

class LifeEventTool(BaseTool):
    """Tool for managing user life events."""
    
    name: str = "life_event"
    description: str = """
    Manage and track important life events for users. 
    Use this tool to record significant life events like birthdays, graduations, job changes, etc.
    """
    args_schema: Type[BaseModel] = LifeEventInput
    dm: Any = None
    event_manager: Any = None  # Add this line to properly declare the field
    
    def __init__(self, data_manager, **kwargs):
        super().__init__(**kwargs)
        self.dm = data_manager
        # Initialize LifeEventManager with the DataManager instance
        object.__setattr__(self, 'event_manager', LifeEventManager(data_manager))
    
    def _run(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the life event tool synchronously."""
        return self._handle_event(kwargs)
    
    async def _arun(self, *args, **kwargs) -> Dict[str, Any]:
        """Execute the life event tool asynchronously."""
        return self._handle_event(kwargs)
    
    def _handle_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle life event operations."""
        action = data.get('action', '').lower()
        user_id = data.get('user_id')
        
        if not user_id:
            return {"status": "error", "message": "User ID is required"}
        
        try:
            if action == 'add':
                return self._add_event(user_id, data)
            elif action == 'get':
                return self._get_event(user_id, data.get('event_id'))
            elif action == 'update':
                return self._update_event(user_id, data)
            elif action == 'delete':
                return self._delete_event(user_id, data.get('event_id'))
            elif action == 'list':
                return self._list_events(user_id, data)
            elif action == 'timeline':
                return self._get_timeline(user_id)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"status": "error", "message": f"Error in life event tool: {str(e)}"}
    
    def _add_event(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new life event."""
        event_data = {
            "user_id": user_id,
            "event_type": data.get('event_type', 'OTHER'),
            "title": data.get('title', 'Untitled Event'),
            "description": data.get('description', ''),
            "start_date": data.get('start_date', datetime.utcnow()),
            "end_date": data.get('end_date'),
            "location": data.get('location'),
            "people_involved": data.get('people_involved', []),
            "impact_level": data.get('impact_level', 5),
            "is_private": data.get('is_private', True),
            "tags": data.get('tags', []),
            "metadata": data.get('metadata', {})
        }
        
        event = self.event_manager.add_event(event_data)
        return {
            "status": "success",
            "message": "Life event added successfully",
            "event": event.dict() if event else None
        }
    
    def _get_event(self, user_id: int, event_id: int) -> Dict[str, Any]:
        """Get a specific event."""
        if not event_id:
            return {"status": "error", "message": "Event ID is required"}
            
        event = self.event_manager.get_event(event_id, user_id)
        if not event:
            return {"status": "error", "message": "Event not found"}
            
        return {
            "status": "success",
            "event": event.dict()
        }
    
    def _update_event(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing event."""
        event_id = data.get('event_id')
        if not event_id:
            return {"status": "error", "message": "Event ID is required for update"}
            
        # Remove None values and action/event_id from update data
        update_data = {k: v for k, v in data.items() 
                      if v is not None and k not in ('action', 'event_id')}
                      
        if not update_data:
            return {"status": "error", "message": "No update data provided"}
            
        event = self.event_manager.update_event(event_id, user_id, update_data)
        if not event:
            return {"status": "error", "message": "Failed to update event"}
            
        return {
            "status": "success",
            "message": "Event updated successfully",
            "event": event.dict()
        }
    
    def _delete_event(self, user_id: int, event_id: int) -> Dict[str, Any]:
        """Delete an event."""
        if not event_id:
            return {"status": "error", "message": "Event ID is required"}
            
        success = self.event_manager.delete_event(event_id, user_id)
        if not success:
            return {"status": "error", "message": "Failed to delete event"}
            
        return {
            "status": "success",
            "message": "Event deleted successfully"
        }
    
    def _list_events(self, user_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """List events with optional filtering."""
        events = self.event_manager.get_user_events(
            user_id=user_id,
            event_type=data.get('event_type'),
            limit=data.get('limit', 50),
            offset=data.get('offset', 0)
        )
        
        return {
            "status": "success",
            "count": len(events),
            "events": [e.dict() for e in events]
        }
    
    def _get_timeline(self, user_id: int) -> Dict[str, Any]:
        """Get a timeline of events grouped by year."""
        timeline = self.event_manager.get_timeline(user_id)
        
        # Convert Pydantic models to dicts for JSON serialization
        timeline_dict = {
            str(year): [e.dict() for e in events] 
            for year, events in timeline.items()
        }
        
        return {
            "status": "success",
            "timeline": timeline_dict
        }


class ClarifyCommunicationInput(BaseModel):
    """Input for clarifying communication between users."""
    text: str = Field(..., description="The text that needs clarification or translation")
    source_language: Optional[str] = Field(None, description="Source language if known")
    target_language: Optional[str] = Field("English", description="Target language (default: English)")
    context: Optional[str] = Field(None, description="Additional context about the conversation")


class ClarifyCommunicationTool(BaseTool):
    """Tool to clarify communication and translate between users who don't understand each other."""
    
    name: str = "clarify_communication"
    description: str = """Use this tool when users don't understand each other or when translation/clarification is needed.
    
    This tool helps with:
    - Translating foreign language text
    - Explaining phrases or cultural context
    - Detecting misunderstandings
    - Providing clear explanations
    - Bridging language barriers
    
    Input should include the text that needs clarification."""
    args_schema: Type[BaseModel] = ClarifyCommunicationInput
    
    def _run(self, text: str, source_language: Optional[str] = None, 
             target_language: str = "English", context: Optional[str] = None) -> Dict[str, Any]:
        """Clarify communication by translating and explaining text."""
        
        # Detect if text contains non-ASCII (foreign language)
        has_foreign_chars = any(ord(char) > 127 for char in text)
        
        # Use LLM to translate and explain
        try:
            clarification_prompt = f"""You are a translation and communication clarification assistant in PROACTIVE MODE.

Text to clarify: "{text}"
Source language: {source_language or "Auto-detect"}
Target language: {target_language}
Context: {context or "General conversation"}

IMPORTANT: Be direct and helpful. DO NOT ask if they want help. PROVIDE the help immediately.

Provide immediately:
1. Direct translation to {target_language} (if foreign language detected)
2. Clear explanation of what was meant
3. Cultural context if relevant
4. Clarification of any ambiguity

Format: Start with the translation/clarification directly. Be concise and clear.
Example: "They said: [translation]. This means [explanation]."

DO NOT say "Would you like me to..." or "I can help..." - JUST HELP."""

            response = llm.invoke(clarification_prompt)
            
            result = {
                "original_text": text,
                "has_foreign_language": has_foreign_chars,
                "clarification": response.content,
                "suggested_response": f"Based on '{text}', here's what they meant: {response.content}"
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Error clarifying communication: {str(e)}",
                "original_text": text
            }
    
    def invoke(self, input_data):
        """Handle tool invocation."""
        if isinstance(input_data, dict):
            return self._run(**input_data)
        elif isinstance(input_data, str):
            return self._run(text=input_data)
        else:
            return {"error": "Invalid input format for clarify_communication"}


clarify_tool = ClarifyCommunicationTool()
format_tool = FormatTool()

tools = [tavily_search_tool, conversation_recall, skill_evaluator, user_preference_tool, LifeEventTool(dm), clarify_tool, format_tool]

memory = InMemorySaver()


class State(TypedDict):
    """
    create State class to keep track of chat
    """

    messages: Annotated[list, add_messages]


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        # Create a dictionary of tools by name
        self.tools_by_name = {}
        for tool in tools:
            if hasattr(tool, "name") and hasattr(tool, "invoke"):
                self.tools_by_name[tool.name] = tool
            elif hasattr(tool, "name"):
                # Handle callable tools
                self.tools_by_name[tool.name] = tool
            elif hasattr(tool, "__name__"):
                # Handle function tools
                self.tools_by_name[tool.__name__] = tool

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")

        outputs = []
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            return {"messages": []}

        for tool_call in message.tool_calls:
            tool_name = tool_call["name"]
            if tool_name not in self.tools_by_name:
                error_msg = f"Tool '{tool_name}' not found. Available tools: {list(self.tools_by_name.keys())}"
                outputs.append(
                    ToolMessage(
                        content=json.dumps({"error": error_msg}),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
                continue

            tool = self.tools_by_name[tool_name]
            try:
                # Handle different tool types
                if hasattr(tool, "invoke"):
                    # For tools with an invoke method (like our custom tools)
                    if tool_name == "tavily_search":
                        # Special handling for Tavily search to ensure proper argument passing
                        if isinstance(tool_call["args"], dict) and "query" in tool_call["args"]:
                            tool_result = tool.invoke(tool_call["args"]["query"])
                        elif isinstance(tool_call["args"], str):
                            tool_result = tool.invoke(tool_call["args"])
                        else:
                            tool_result = tool.invoke(tool_call["args"])
                    else:
                        # For other tools with invoke method
                        tool_result = tool.invoke(tool_call["args"])
                elif callable(tool):
                    # For callable tools (like the original TavilySearch)
                    tool_result = tool.invoke(tool_call["args"]["query"] if isinstance(tool_call["args"], dict) else tool_call["args"])
                else:
                    tool_result = {"error": f"Tool {tool_name} is not callable"}

                # Format the tool result for readability
                formatted_result = ResponseFormatter.format_tool_result(tool_name, tool_result)
                formatted_result = ResponseFormatter.clean_response(formatted_result)
                
                outputs.append(
                    ToolMessage(
                        content=formatted_result,
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )
            except Exception as e:
                outputs.append(
                    ToolMessage(
                        content=json.dumps(
                            {"error": f"Error calling tool {tool_name}: {str(e)}"}
                        ),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                )

        return {"messages": outputs}


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
    create ai_chatagent object
    """

    def __init__(self, user: User, llm):
        self.user = user
        self.preferences = user.preferences or {}
        self.temperature = user.temperature or 0.7
        
        # ✅ Initialize O-T-E Logger for observability
        self.ote_logger = get_logger()
        self.request_start_time = None
        self.current_request_id = None
        self.skills = dm.get_skills_for_user(user.id) or {}
        self.training = dm.get_training_for_user(user.id) or {}
        self.user_profile = {
            "username": user.username,
            "skills": self.skills,
            "training": self.training,
            "preferences": self.preferences,
            "temperature": self.temperature,
        }
        self.used_tools_in_session = set()  # Track tools used in current session
        self.last_user_message = None  # Track the last user message to detect new conversations
        
        # Initialize tool instances
        self.tavily_search = TavilySearchTool(search_tool=tool_1)
        self.conversation_tool = ConversationRecallTool(dm)
        self.skill_evaluator_tool = SkillEvaluator(dm)
        self.user_preference_tool = UserPreferenceTool(dm)
        self.clarify_tool = ClarifyCommunicationTool()
        
        # Initialize tools configuration for LLM
        self.tools = [
            {
                "name": "tavily_search",
                "description": "Search the web for information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query"}
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "recall_last_conversation",
                "description": "Recall the last conversation from memory. Use this when the user asks about previous conversations or context.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user whose conversation to retrieve",
                        }
                    },
                    "required": ["user_id"],
                },
            },
            {
                "name": "skill_evaluator",
                "description": "Evaluate user skills based on chat interactions and manage training.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "The ID of the user whose skills to evaluate",
                        },
                        "message": {
                            "type": "string",
                            "description": "The user's message to evaluate",
                        },
                    },
                    "required": ["user_id", "message"],
                },
            },
            {
                "name": "format_output",
                "description": "Format raw data (JSON, dicts, API responses) into beautiful human-readable text. ALWAYS use this when you receive raw JSON or dict data from other tools before showing it to users.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "The raw data to format (JSON string or dict)",
                        },
                        "data_type": {
                            "type": "string",
                            "description": "Type of data: 'weather', 'search', 'conversation', or 'auto' (default)",
                            "enum": ["weather", "search", "conversation", "auto"],
                        },
                    },
                    "required": ["data"],
                },
            },
            {
                "name": "user_preference",
                "description": "Save and retrieve personal user data like name, DOB, interests, skills, preferences. Use this to remember important information about the user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "description": "Action to perform: 'get', 'set', or 'delete'",
                            "enum": ["get", "set", "delete"],
                        },
                        "user_id": {
                            "type": "integer",
                            "description": "The user ID",
                        },
                        "preference_type": {
                            "type": "string",
                            "description": "Category: 'personal_info', 'interests', 'skills', 'preferences'",
                        },
                        "preference_key": {
                            "type": "string",
                            "description": "Specific key: 'name', 'dob', 'favorite_topic', etc.",
                        },
                        "preference_value": {
                            "type": "string",
                            "description": "Value to set",
                        },
                    },
                    "required": ["action", "user_id"],
                },
            },
            {
                "name": "clarify_communication",
                "description": "Translate foreign languages and clarify misunderstandings between users. Use this when detecting communication barriers, cultural differences, or language issues.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The text to translate/clarify",
                        },
                        "source_language": {
                            "type": "string",
                            "description": "Source language (optional, auto-detect)",
                        },
                        "target_language": {
                            "type": "string",
                            "description": "Target language (default: English)",
                        },
                    },
                    "required": ["text"],
                },
            },
        ]
        
        # Initialize LifeEventTool if DataManager is available
        self.life_event_tool = LifeEventTool(dm) if 'dm' in globals() else None
        
        # Initialize FormatTool for making output human-readable
        self.format_tool = FormatTool()
        
        # Create a mapping of tool names to their instances
        self.tool_instances = {
            "tavily_search": self.tavily_search,
            "recall_last_conversation": self.conversation_tool,
            "skill_evaluator": self.skill_evaluator_tool,
            "user_preference": self.user_preference_tool,
            "clarify_communication": self.clarify_tool,
            "life_event": self.life_event_tool if self.life_event_tool else None,
            "format_output": self.format_tool
        }
        
        # Remove any None values from tool_instances
        self.tool_instances = {k: v for k, v in self.tool_instances.items() if v is not None}
        
        # ✅ FIX: Bind actual tool instances (BaseTool objects) to LLM, not dictionaries!
        tool_list = list(self.tool_instances.values())
        
        # Check if using Gemini (has compatibility issues with some tools)
        llm_model_name = getattr(llm, 'model_name', getattr(llm, 'model', ''))
        is_gemini = 'gemini' in str(llm_model_name).lower()
        
        if is_gemini:
            # Gemini has stricter tool schema requirements
            # All tools now have proper args_schema defined!
            print(f"✅ Gemini detected - using ALL {len(tool_list)} tools (now compatible!)")
            try:
                self.llm_with_tools = llm.bind_tools(tool_list)
            except Exception as e:
                print(f"⚠️  Gemini tool binding failed: {e}")
                print("⚠️  Using Gemini without tools")
                self.llm_with_tools = llm
        else:
            # OpenAI, Claude, etc - use all tools
            self.llm_with_tools = llm.bind_tools(tool_list)

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
        """Process a message and return a response.
        
        Args:
            state: The current conversation state containing messages
            
        Returns:
            dict: A dictionary with a single 'messages' key containing the AI's response
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
                            return {"messages": [{"role": "assistant", 
                                              "content": f"I've already searched for that information. Based on the results I found, let me provide you with the answer."}]}
            
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
                        return {"messages": [{"role": "assistant", 
                                          "content": f"I've already searched for that information. Based on the results I found earlier, let me provide you with the answer."}]}
                
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
            system_prompt = f"""You are an AI Social Coach and Communication Assistant for user ID: {self.user.id} (Username: {self.user.username})

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

🚫 **CRITICAL: NEVER REPEAT TOOL CALLS & ALWAYS USE format_output**
⚠️  IMPORTANT RULES:
1. **After getting search/tool results → IMMEDIATELY call format_output, then STOP**
   - See weather data in conversation? → Call format_output with data and data_type=weather
   - See search results? → Call format_output with data and data_type=search
   - After format_output returns → STOP and respond to user
   - DO NOT call tavily_search or any other tool after format_output
   
2. **NEVER call the same tool twice**
   - If you see a ToolMessage with weather/search data → Use format_output IMMEDIATELY
   - ONE search per question, ONE format_output call, then RESPOND
   - Do NOT search again, do NOT refine queries, do NOT call more tools
   
3. **Detect when you already have the answer:**
   - See ToolMessage with weather data? → You HAVE the answer → Call format_output → DONE
   - See ToolMessage with search results? → You HAVE the answer → Call format_output → DONE
   - DO NOT call tavily_search if you see a recent ToolMessage with relevant data

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
            
            sys_msg = SystemMessage(content=system_prompt)
            
            # Convert messages to the format expected by the LLM
            messages_for_llm = [sys_msg]
            
            # Add historical context (last 20 messages from DB)
            for hist_msg in historical_messages:
                if isinstance(hist_msg, dict) and 'content' in hist_msg:
                    messages_for_llm.append({
                        'role': hist_msg.get('role', 'user'),
                        'content': hist_msg['content']
                    })
            
            # Add current state messages
            messages = state.get('messages', []) if isinstance(state, dict) else state.messages
            for msg in messages:  # Include all current messages
                if hasattr(msg, 'content'):
                    # Handle LangChain message objects
                    role = 'user' if isinstance(msg, HumanMessage) else 'assistant'
                    messages_for_llm.append({
                        'role': role,
                        'content': msg.content
                    })
                    print(f"Added message to LLM context - Role: {role}, Content: {msg.content[:100]}...")
                elif isinstance(msg, dict) and 'content' in msg:
                    # Handle dictionary messages
                    messages_for_llm.append({
                        'role': msg.get('role', 'user'),
                        'content': msg['content']
                    })
                    print(f"Added dict message to LLM context - Role: {msg.get('role', 'user')}, Content: {msg['content'][:100]}...")
            
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
                self.ote_logger.log_llm_call(
                    request_id=self.current_request_id,
                    model=getattr(response, 'model', 'gpt-4o-mini'),
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
                        from langchain_core.messages import AIMessage
                        stop_message = AIMessage(
                            content="I've already searched for this information. Based on the search results above, I can answer your question. Please let me know if you need any clarification or have a different question."
                        )
                        return {"messages": [stop_message]}
                
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
                            # Check if result was already formatted
                            if not previous_result.startswith('{'):
                                # Already formatted, just return it
                                print("✅ Previous result already formatted, returning it")
                                from langchain_core.messages import AIMessage
                                return {"messages": [AIMessage(content=previous_result)]}
                            else:
                                # Raw data, need to format it
                                print("🔧 Previous result is raw data, calling format_output")
                                # Force format_output call instead
                                from langchain_core.messages import AIMessage
                                format_call = {
                                    'name': 'format_output',
                                    'args': {'data': previous_result, 'data_type': 'weather' if 'location' in previous_result else 'search'},
                                    'id': 'duplicate_format_' + str(hash(previous_result)),
                                    'type': 'tool_call'
                                }
                                format_message = AIMessage(content='', tool_calls=[format_call])
                                return {"messages": [format_message]}
                        
                        # Fallback: generic message
                        print("🔄 No previous result found, returning generic message")
                        redirect_content = (
                            "I already have this information. Let me provide it to you based on my previous search."
                        )
                        
                        from langchain_core.messages import AIMessage
                        redirect_message = AIMessage(content=redirect_content)
                        return {"messages": [redirect_message]}
                
                print(f"✅ No duplicates - approving tool execution")
                print("="*70)
                print(f"\n=== LLM GENERATED TOOL CALLS - RETURNING TO GRAPH ===")
                for tool_call in response.tool_calls:
                    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown')
                    print(f"   Tool: {tool_name}")
                # Return the AIMessage with tool_calls - graph will route to tools node
                return {"messages": [response]}
            
            # Regular response (no tool calls) - return it
            return {"messages": [response]}
                
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
        Route to the appropriate tool based on the last message.
        Returns "tools" if tool_calls are present, otherwise END.
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
    
    def build_graph(self):
        from langgraph.graph import StateGraph
        
        # Initialize a new graph
        graph_builder = StateGraph(State)
        
        # Add nodes
        graph_builder.add_node("chatbot", self.chatbot)
        graph_builder.add_node("tools", tool_node)
        
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
