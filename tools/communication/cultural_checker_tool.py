"""
Cultural & Political Standards Checker Tool

LOCATION: tools/communication/cultural_checker_tool.py
PURPOSE: Check cultural and political language standards to avoid misunderstandings

FEATURES:
    - Check messages for cultural sensitivity
    - Verify political correctness across cultures
    - Use web search to get latest standards
    - Provide suggestions for better phrasing
"""

from typing import Type, Optional, Dict, Any, ClassVar
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from app.ote_logger import get_logger

logger = get_logger()

# Import web search
try:
    from langchain_tavily import TavilySearch
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    logger.logger.warning("⚠️  Tavily search not available")
    WEB_SEARCH_AVAILABLE = False


class CulturalCheckerInput(BaseModel):
    """Input schema for CulturalChecker."""
    message: str = Field(description="Message to check for cultural/political sensitivity")
    cultural_context: Optional[str] = Field(
        default=None, 
        description="Cultural context (e.g., 'Western', 'Asian', 'Middle Eastern')"
    )
    user_country: Optional[str] = Field(
        default=None,
        description="User's country for specific cultural norms"
    )


class CulturalStandardsChecker(BaseTool):
    """
    Check messages for cultural and political sensitivity.
    
    This tool helps avoid cultural misunderstandings in chat rooms by:
    - Analyzing messages for potentially offensive content
    - Checking against current cultural/political standards
    - Providing alternative phrasings
    - Warning about culturally sensitive topics
    
    Attributes:
        name: Tool name for LLM
        description: Tool description for LLM
        args_schema: Pydantic schema for validation
        search_tool: Web search tool for latest standards
    """
    
    name: str = "check_cultural_standards"
    description: str = (
        "Check if a message respects cultural and political standards to avoid "
        "misunderstandings in chat rooms. Returns warnings and suggestions."
    )
    args_schema: Type[BaseModel] = CulturalCheckerInput
    search_tool: Optional[Any] = None
    
    # Known sensitive topics that require careful handling
    # ClassVar indicates this is a class-level constant, not a field
    SENSITIVE_TOPICS: ClassVar[Dict[str, list]] = {
        "religion": ["god", "allah", "buddha", "prayer", "worship", "bible", "quran"],
        "politics": ["election", "president", "government", "democracy", "socialism"],
        "race": ["race", "ethnic", "minority", "indigenous"],
        "gender": ["gender", "lgbtq", "transgender", "pronouns"],
        "disability": ["disabled", "handicapped", "retarded", "crippled"],
        "age": ["old", "elderly", "boomer", "millennial"]
    }
    
    # Potentially offensive terms (basic list - web search provides more)
    # ClassVar indicates this is a class-level constant, not a field
    WATCH_WORDS: ClassVar[list] = [
        "retarded", "crippled", "handicapped", "oriental", "colored",
        "illegal alien", "third world", "primitive"
    ]
    
    def __init__(self):
        """Initialize CulturalStandardsChecker with web search."""
        super().__init__()
        
        if WEB_SEARCH_AVAILABLE:
            try:
                self.search_tool = TavilySearch(max_results=5)
                logger.logger.info("✅ Cultural checker initialized with web search")
            except Exception as e:
                logger.logger.warning(f"Could not initialize web search: {e}")
                self.search_tool = None
        else:
            self.search_tool = None
    
    def _run(self, message: str, cultural_context: Optional[str] = None, 
             user_country: Optional[str] = None) -> Dict[str, Any]:
        """
        Check message for cultural/political sensitivity.
        
        Args:
            message: Message to check
            cultural_context: Cultural context for evaluation
            user_country: User's country for specific norms
            
        Returns:
            Dictionary with warnings, sensitivity score, and suggestions
        """
        try:
            logger.logger.info(f"Checking cultural standards for message: {message[:50]}...")
            
            result = {
                "status": "success",
                "message_safe": True,
                "sensitivity_score": 0,  # 0-10, higher = more sensitive
                "warnings": [],
                "suggestions": [],
                "sensitive_topics": []
            }
            
            message_lower = message.lower()
            
            # 1. Check for sensitive topics
            for topic, keywords in self.SENSITIVE_TOPICS.items():
                if any(keyword in message_lower for keyword in keywords):
                    result["sensitive_topics"].append(topic)
                    result["sensitivity_score"] += 2
                    result["warnings"].append(
                        f"⚠️  Message contains {topic}-related content. "
                        f"Please be respectful of different {topic}al beliefs."
                    )
            
            # 2. Check for potentially offensive terms
            found_watch_words = [word for word in self.WATCH_WORDS if word in message_lower]
            if found_watch_words:
                result["message_safe"] = False
                result["sensitivity_score"] += 5
                result["warnings"].append(
                    f"❌ Message contains potentially offensive terms: {', '.join(found_watch_words)}"
                )
                result["suggestions"].append(
                    "Consider rephrasing to use more respectful language."
                )
            
            # 3. Check for all-caps (can be seen as shouting)
            if message.isupper() and len(message) > 10:
                result["sensitivity_score"] += 1
                result["warnings"].append(
                    "⚠️  Message is in ALL CAPS, which can be perceived as shouting."
                )
                result["suggestions"].append(
                    "Consider using normal capitalization for a friendlier tone."
                )
            
            # 4. Use web search for latest cultural standards (if sensitive topic detected)
            if result["sensitive_topics"] and self.search_tool:
                latest_standards = self._check_latest_standards(
                    message, 
                    result["sensitive_topics"],
                    cultural_context,
                    user_country
                )
                if latest_standards:
                    result["latest_standards"] = latest_standards
            
            # Cap sensitivity score at 10
            result["sensitivity_score"] = min(result["sensitivity_score"], 10)
            
            # Overall assessment
            if result["sensitivity_score"] >= 7:
                result["message_safe"] = False
                result["overall_assessment"] = "⚠️  HIGH SENSITIVITY - Review before sending"
            elif result["sensitivity_score"] >= 4:
                result["overall_assessment"] = "⚠️  MEDIUM SENSITIVITY - Consider rephrasing"
            else:
                result["overall_assessment"] = "✅ Message appears culturally appropriate"
            
            logger.logger.info(
                f"Cultural check complete: score={result['sensitivity_score']}, "
                f"safe={result['message_safe']}"
            )
            
            return result
            
        except Exception as e:
            logger.logger.error(f"Error in cultural standards check: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Could not perform cultural standards check: {str(e)}",
                "message_safe": True  # Default to safe on error
            }
    
    def _check_latest_standards(self, message: str, topics: list, 
                               cultural_context: Optional[str],
                               user_country: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Use web search to check latest cultural/political standards.
        
        Args:
            message: Original message
            topics: Detected sensitive topics
            cultural_context: Cultural context
            user_country: User's country
            
        Returns:
            Dictionary with search results or None
        """
        try:
            # Build search query
            topics_str = " ".join(topics)
            context_str = f"{cultural_context} " if cultural_context else ""
            country_str = f"{user_country} " if user_country else ""
            
            query = (
                f"{country_str}{context_str}cultural sensitivity {topics_str} "
                f"communication standards 2024 2025"
            )
            
            logger.logger.info(f"Searching latest standards: {query}")
            
            # Perform search
            results = self.search_tool.invoke(query)
            
            return {
                "query": query,
                "results": str(results)[:500],  # Limit to 500 chars
                "note": "Recent cultural communication standards from web search"
            }
            
        except Exception as e:
            logger.logger.error(f"Error searching latest standards: {e}")
            return None
    
    async def _arun(self, *args, **kwargs):
        """Async version calls sync version."""
        return self._run(*args, **kwargs)
