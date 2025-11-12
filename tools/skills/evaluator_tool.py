"""
Skill Evaluator Tool with OTE Compliance

LOCATION: tools/skills/evaluator_tool.py
PURPOSE: Evaluate user social skills and manage training with OTE tracking

TRACE POINTS:
    - VALIDATE: Input validation
    - WEB_RESEARCH: Fetch latest empathy research
    - ANALYZE: Message skill analysis
    - DB_GET_SKILLS: Retrieve current skill levels
    - DB_UPDATE_SKILL: Update skill level in database
    - SUGGESTIONS: Generate skill suggestions

DEPENDENCIES:
    - datamanager.DataManager
    - skill_agents (SkillEvaluationOrchestrator)
    - langchain_tavily.TavilySearch
    
OTE COMPLIANCE:
    - Observability: All operations logged with timing
    - Traceability: Trace markers for each analysis step
    - Evaluation: Skill detection metrics, performance tracking
"""

import atexit
from typing import Type, Optional, Any, Dict, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from datamanager.data_manager import DataManager
from app.utils import get_logger, observe, traceable, evaluate

# Get logger for this module
logger = get_logger(__name__)

# Import skill evaluation orchestrator
try:
    from skill_agents import (
        get_evaluation_orchestrator,
        stop_evaluation_orchestrator,
        SkillEvaluationOrchestrator,
    )
    SKILL_AGENTS_AVAILABLE = True
    logger.info("✅ Skill agents available")
except ImportError:
    logger.warning("⚠️  Skill agents module not found. Limited functionality.")
    SKILL_AGENTS_AVAILABLE = False
    SkillEvaluationOrchestrator = None

# Import web search for research
try:
    from langchain_tavily import TavilySearch
    tavily_search = TavilySearch(max_results=10)
    WEB_SEARCH_AVAILABLE = True
    logger.info("✅ Web search available")
except ImportError:
    logger.warning("⚠️  Tavily search not available. Web research disabled.")
    WEB_SEARCH_AVAILABLE = False
    tavily_search = None


class SkillEvaluatorInput(BaseModel):
    """
    Input schema for SkillEvaluator.
    
    Attributes:
        user_id: The ID of the user to evaluate
        message: Single message to evaluate (optional if messages provided)
        messages: List of messages to evaluate (optional if message provided)
        cultural_context: User's cultural background (default: Western)
        use_web_research: Whether to fetch latest research (default: True)
    """
    user_id: int = Field(description="The ID of the user to evaluate")
    message: Optional[str] = Field(default=None, description="Single message to evaluate")
    messages: Optional[List[str]] = Field(default=None, description="List of messages to evaluate")
    cultural_context: Optional[str] = Field(default="Western", description="User's cultural background")
    use_web_research: Optional[bool] = Field(default=True, description="Whether to fetch latest research")


class SkillEvaluator(BaseTool):
    """
    Evaluates user social skills based on chat interactions with OTE tracking.
    
    This tool analyzes messages for social skills demonstration (active listening,
    empathy, clarity, engagement) and tracks progress over time. Optionally
    fetches latest research to ensure evaluation standards are current.
    
    OTE Compliance:
        - All evaluations observed with timing
        - Trace markers show analysis flow
        - Success/failure rates tracked per skill
        - Web research performance monitored
    
    Attributes:
        name: Tool name for LLM
        description: Tool description for LLM
        args_schema: Pydantic schema for validation
        dm: DataManager instance
        orchestrator: Multi-agent skill evaluation orchestrator
        skills: Dictionary of skills and their keywords
    
    Example:
        >>> tool = SkillEvaluator(data_manager)
        >>> result = tool.run({
        ...     "user_id": 123,
        ...     "message": "I understand how you feel",
        ...     "cultural_context": "Western"
        ... })
        >>> print(result["message_analysis"]["detected_skills"])
        [{"skill": "empathy", "detected": True}]
    """
    
    name: str = "skill_evaluator"
    description: str = (
        "Evaluate user skills based on chat interactions and manage training. "
        "Analyzes messages for active listening, empathy, clarity, and engagement."
    )
    args_schema: Type[BaseModel] = SkillEvaluatorInput
    dm: DataManager = None
    orchestrator: Optional[Any] = None  # SkillEvaluationOrchestrator or None
    skills: Dict[str, Dict[str, Any]] = {}

    def __init__(self, data_manager: DataManager):
        """
        Initialize SkillEvaluator with orchestrator and skill definitions.
        
        Args:
            data_manager: DataManager instance for database operations
        """
        super().__init__()
        self.dm = data_manager
        
        logger.trace("INIT", "Initializing skill evaluator")
        
        # Initialize orchestrator if available
        if SKILL_AGENTS_AVAILABLE:
            try:
                self.orchestrator = get_evaluation_orchestrator(data_manager)
                logger.info("✅ Skill orchestrator initialized")
            except Exception as e:
                logger.error(f"Failed to initialize orchestrator: {e}")
                self.orchestrator = None
        else:
            self.orchestrator = None
        
        # Register cleanup handler
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
        
        logger.observe("init_complete", skills=len(self.skills), orchestrator=bool(self.orchestrator))

    def cleanup(self, user_id: int = None):
        """
        Clean up resources when evaluator is destroyed.
        
        Args:
            user_id: Optional user ID to generate final skill suggestions
        """
        logger.trace("CLEANUP", "Cleaning up skill evaluator resources")
        
        if self.orchestrator:
            try:
                if user_id is not None:
                    suggestions = self.get_skill_suggestions(user_id)
                    if suggestions:
                        print("\nSkill Suggestions:")
                        for suggestion in suggestions:
                            print(f"- {suggestion['skill']}: {suggestion['suggestion']}")
            except Exception as e:
                logger.error(f"Error generating skill suggestions: {e}")
                
            if SKILL_AGENTS_AVAILABLE:
                stop_evaluation_orchestrator()
                logger.info("✅ Orchestrator stopped")

    @observe("skill_evaluation")
    @evaluate(detect_anomalies=True)
    def _run(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Run skill evaluation with OTE tracking.
        
        TRACE PATH:
            1. VALIDATE → Input validation
            2. WEB_RESEARCH → Fetch latest research (optional)
            3. DB_GET_SKILLS → Get current skill levels
            4. ANALYZE → Analyze message for skills
            5. DB_UPDATE_SKILL → Update skills in database
            6. SUGGESTIONS → Generate improvement suggestions
        
        Args:
            user_id: The ID of the user to evaluate
            message: The message to evaluate (optional if messages provided)
            messages: List of messages to evaluate (optional if message provided)
            cultural_context: User's cultural background (default: Western)
            use_web_research: Whether to fetch latest research (default: True)

        Returns:
            Dict containing skill scores, suggestions, and latest research
            
        Raises:
            No exceptions raised - all errors returned in response dict
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
            
            # TRACE POINT 1: Validation
            logger.trace("VALIDATE", f"Validating input for user={user_id}, messages={len(messages)}")
            
            if not user_id:
                logger.warning("Validation failed: missing user_id")
                return {"status": "error", "message": "User ID is required"}
                
            if not messages:
                logger.warning("Validation failed: no messages provided")
                return {"status": "error", "message": "No message or messages provided"}
            
            # TRACE POINT 2: Web research
            latest_standards = None
            if use_web_research and WEB_SEARCH_AVAILABLE and tavily_search:
                latest_standards = self._fetch_research(cultural_context)
            
            # TRACE POINT 3: Get current skill levels BEFORE analysis
            logger.trace("DB_GET_SKILLS", f"Retrieving current skills for user={user_id}")
            current_skills_before = self.get_skill_suggestions(user_id)
            
            # TRACE POINT 4: Analyze message for skill demonstration
            logger.trace("ANALYZE", f"Analyzing message for skills")
            analysis = self._analyze_message_skills(
                message if isinstance(message, str) else str(messages),
                cultural_context
            )
            
            # TRACE POINT 5: Update database with detected skills
            skills_updated = self._update_detected_skills(user_id, analysis)
            
            # TRACE POINT 6: Get updated skill levels AFTER analysis
            logger.trace("SUGGESTIONS", f"Generating skill suggestions")
            current_skills_after = self.get_skill_suggestions(user_id)
            
            logger.observe(
                "evaluation_complete",
                skills_detected=analysis.get('skill_count', 0),
                skills_updated=len(skills_updated),
                success=True
            )
            
            return {
                "status": "success",
                "message": f"Skill evaluation completed. {len(skills_updated)} skills updated.",
                "current_skills": current_skills_after,
                "skills_updated": skills_updated,
                "message_analysis": analysis,
                "latest_standards": latest_standards,
                "cultural_context": cultural_context,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"Error in skill evaluation: {str(e)}", exc_info=True)
            logger.observe("evaluation_complete", success=False)
            return {
                "status": "error",
                "message": f"An error occurred while evaluating skills: {str(e)}",
                "current_skills": self.get_skill_suggestions(user_id) if 'user_id' in locals() else []
            }
    
    @traceable()
    @observe("web_research")
    def _fetch_research(self, cultural_context: str) -> Optional[Dict[str, Any]]:
        """
        Fetch latest empathy and social skills research from web.
        
        TRACE PATH:
            WEB_RESEARCH → API call → Result processing
        
        Args:
            cultural_context: Cultural context for research query
            
        Returns:
            Dictionary with research query and results, or None if failed
        """
        logger.trace("WEB_RESEARCH", f"Fetching research for context={cultural_context}")
        
        try:
            research_query = f"latest {cultural_context} empathy social skills research 2024 2025"
            research_result = tavily_search.invoke(research_query)
            
            latest_standards = {
                "query": research_query,
                "research": str(research_result)[:500],  # Limit to 500 chars
                "updated": "2025-11-12"
            }
            
            logger.observe("research_fetched", query_length=len(research_query), success=True)
            return latest_standards
            
        except Exception as e:
            logger.error(f"Web research failed: {e}")
            logger.observe("research_fetched", success=False)
            return None
    
    @traceable()
    def _analyze_message_skills(self, message: str, cultural_context: str = "Western") -> Dict[str, Any]:
        """
        Analyze a message for social skill demonstration.
        
        Uses keyword matching to detect skills in the message.
        More sophisticated analysis could use ML/NLP.
        
        Args:
            message: The message to analyze
            cultural_context: Cultural context for evaluation
            
        Returns:
            Analysis results with detected skills and metadata
        """
        logger.trace("ANALYZE", f"Analyzing message of length={len(message)}")
        
        message_lower = message.lower()
        detected_skills = []
        
        for skill_name, data in self.skills.items():
            keywords = data.get('keywords', [])
            keywords_found = [kw for kw in keywords if kw.lower() in message_lower]
            
            if keywords_found:
                detected_skills.append({
                    "skill": skill_name,
                    "detected": True,
                    "keywords_found": keywords_found
                })
                logger.trace("SKILL_DETECTED", f"Detected {skill_name} via keywords={keywords_found}")
        
        analysis = {
            "message_length": len(message),
            "detected_skills": detected_skills,
            "skill_count": len(detected_skills),
            "cultural_context": cultural_context,
            "needs_improvement": len(detected_skills) < 2  # Less than 2 skills detected
        }
        
        logger.observe("analysis_complete", skills_detected=len(detected_skills))
        return analysis
    
    @traceable()
    @observe("update_skills")
    def _update_detected_skills(self, user_id: int, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update database with detected skills.
        
        TRACE PATH:
            For each detected skill:
                DB_GET_SKILL → DB_UPDATE_SKILL
        
        Args:
            user_id: User ID
            analysis: Analysis results from _analyze_message_skills
            
        Returns:
            List of updated skills with old/new levels
        """
        detected_skills = analysis.get('detected_skills', [])
        skills_updated = []
        
        if detected_skills:
            for skill_obj in detected_skills:
                try:
                    skill_name = skill_obj.get('skill') if isinstance(skill_obj, dict) else str(skill_obj)
                    
                    logger.trace("DB_UPDATE_SKILL", f"Updating skill={skill_name} for user={user_id}")
                    
                    # Get or create the skill
                    skill = self.dm.get_or_create_skill(skill_name)
                    if skill:
                        # Get current level
                        current_level = self.dm.get_skilllevel_for_user(user_id, skill.id) or 0
                        
                        # Increment level (max 10)
                        new_level = min(current_level + 1, 10)
                        
                        # Update in database
                        self.dm.set_skill_for_user(user_id, skill, new_level)
                        skills_updated.append({
                            "skill": skill_name,
                            "old_level": current_level,
                            "new_level": new_level,
                            "improved": new_level > current_level
                        })
                        logger.info(f"✅ Updated {skill_name}: {current_level} → {new_level}")
                except Exception as e:
                    logger.error(f"Failed to update skill {skill_name}: {e}")
        
        logger.observe("skills_updated", count=len(skills_updated))
        return skills_updated
    
    @traceable()
    def get_skill_suggestions(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get current skills and suggestions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of dictionaries containing skill information and suggestions
        """
        logger.trace("SUGGESTIONS", f"Generating suggestions for user={user_id}")
        
        suggestions = []
        try:
            for skill_name, data in self.skills.items():
                skill = self.dm.get_or_create_skill(skill_name)
                if not skill:
                    continue
                    
                level = self.dm.get_skilllevel_for_user(user_id, skill.id)
                if level is None:
                    level = 0
                    
                # Build suggestion
                suggestion = {
                    "skill": skill_name,
                    "current_level": level,
                    "max_level": 10,
                    "description": data.get("description", "No description available"),
                    "suggestion": f"Try using phrases like: {', '.join(data.get('keywords', ['practice more'])[:2])}..." if data.get('keywords') else "Keep practicing to improve this skill",
                    "needs_improvement": level < 7
                }
                
                # Add feedback based on level
                if level >= 8:
                    suggestion["feedback"] = "Excellent! You've mastered this skill."
                elif level >= 5:
                    suggestion["feedback"] = "Good progress! Keep it up!"
                else:
                    suggestion["feedback"] = "Let's work on improving this skill."
                
                suggestions.append(suggestion)
                
            # Sort by level (lowest first)
            suggestions.sort(key=lambda x: x["current_level"])
            
            logger.observe("suggestions_generated", count=len(suggestions))
            
        except Exception as e:
            logger.error(f"Error generating skill suggestions: {e}", exc_info=True)
            return [{
                "status": "error",
                "message": "Could not retrieve skill information. Please try again later."
            }]
            
        return suggestions
    
    async def _arun(self, *args, **kwargs):
        """
        Async version of run.
        
        Note:
            Currently calls sync version. Can be optimized for async operations.
        """
        return self._run(*args, **kwargs)
