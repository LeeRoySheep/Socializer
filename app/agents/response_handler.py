"""
Response Handler with OTE Compliance

LOCATION: app/agents/response_handler.py
PURPOSE: Provider-agnostic response formatting and fallback generation with OTE tracking

TRACE POINTS:
    - VALIDATE: Response validation
    - CHECK_EMPTY: Empty response detection
    - FORMAT: Response formatting
    - EXTRACT_TOOL: Tool result extraction
    - FALLBACK: Fallback generation
    - MODEL_DETECT: Model name detection

DEPENDENCIES:
    - langchain_core.messages (AIMessage, ToolMessage)
    
OTE COMPLIANCE:
    - Observability: All operations logged with timing
    - Traceability: Trace markers for response flow
    - Evaluation: Response quality metrics, empty response rates
"""

from typing import Any, Dict, Optional, List, Tuple
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage

from app.utils import get_logger, observe, traceable

# Get logger for this module
logger = get_logger(__name__)


class ResponseHandler:
    """
    Provider-agnostic response handler with OTE tracking.
    
    Handles response formatting, empty response detection, fallback generation,
    and tool result extraction for ALL LLM providers (OpenAI, Claude, Gemini, etc.).
    
    OTE Compliance:
        - All operations observed with timing
        - Trace markers show response flow
        - Empty response rates tracked
        - Format success/failure metrics
    
    Attributes:
        empty_patterns: Set of patterns that indicate empty responses
    
    Example:
        >>> handler = ResponseHandler()
        >>> if handler.is_empty_response(response):
        ...     fallback = handler.create_response_with_fallback(response, messages)
        >>> formatted = handler.format_tool_result(result, "web_search")
    """
    
    # Patterns that indicate an empty response
    EMPTY_PATTERNS = {'', '```', '\n```', '`', '\n', ' ', '  ', '\t'}
    
    def __init__(self):
        """Initialize ResponseHandler with OTE tracking."""
        logger.trace("INIT", "ResponseHandler initialized")
        logger.observe("init_complete", empty_patterns=len(self.EMPTY_PATTERNS))
    
    @traceable()
    @observe("check_empty_response")
    def is_empty_response(self, response: Any) -> bool:
        """
        Check if an AI response is effectively empty.
        
        TRACE PATH:
            CHECK_EMPTY → Extract content → Pattern matching
        
        Args:
            response: The AI message to check (AIMessage, dict, or string)
            
        Returns:
            bool: True if response is empty, False otherwise
        """
        logger.trace("CHECK_EMPTY", f"Checking response type: {type(response)}")
        
        if not response:
            logger.observe("empty_check_result", is_empty=True, reason="null_response")
            return True
        
        # Extract content from various formats
        content = self._extract_content(response)
        
        if not content:
            logger.observe("empty_check_result", is_empty=True, reason="no_content")
            return True
        
        # Check against empty patterns
        stripped = content.strip()
        if stripped in self.EMPTY_PATTERNS:
            logger.observe("empty_check_result", is_empty=True, reason="empty_pattern")
            return True
        
        # Check if it's just whitespace
        if not stripped:
            logger.observe("empty_check_result", is_empty=True, reason="whitespace_only")
            return True
        
        logger.observe("empty_check_result", is_empty=False, content_length=len(content))
        return False
    
    @traceable()
    def _extract_content(self, message: Any) -> str:
        """
        Extract text content from a message in any format.
        
        Handles:
        - AIMessage objects (LangChain)
        - Dictionary with 'content' key
        - Raw strings
        - Other objects (str() conversion)
        
        Args:
            message: The message object
            
        Returns:
            str: The extracted content
        """
        if hasattr(message, 'content'):
            return str(message.content)
        elif isinstance(message, dict):
            return str(message.get('content', ''))
        else:
            return str(message)
    
    @traceable()
    @observe("format_tool_result")
    def format_tool_result(self, tool_result: Any, tool_name: str) -> str:
        """
        Format a tool result into a human-readable string.
        
        TRACE PATH:
            FORMAT → Type detection → Tool-specific formatting
        
        Supports:
        - skill_evaluator: Detailed skill analysis
        - web_search/tavily_search: Search results
        - life_event: Event information
        - user_preference: Preference data
        - Generic tools: Automatic formatting
        
        Args:
            tool_result: The result from the tool
            tool_name: Name of the tool that produced the result
            
        Returns:
            str: Formatted result string
        """
        logger.trace("FORMAT", f"Formatting {tool_name} result, type={type(tool_result)}")
        
        # Handle dictionary results
        if isinstance(tool_result, dict):
            # Error handling
            if 'error' in tool_result:
                error_msg = f"Error from {tool_name}: {tool_result.get('error', 'Unknown error')}"
                logger.warning(f"Tool error: {error_msg}")
                logger.observe("format_result", tool=tool_name, success=False, has_error=True)
                return error_msg
            
            # Tool-specific formatting
            formatted = self._format_by_tool(tool_result, tool_name)
            logger.observe("format_result", tool=tool_name, success=True, length=len(formatted))
            return formatted
        
        # Handle string results
        if isinstance(tool_result, str):
            logger.observe("format_result", tool=tool_name, success=True, type="string")
            return tool_result
        
        # Handle list results
        if isinstance(tool_result, list):
            if not tool_result:
                logger.observe("format_result", tool=tool_name, success=True, empty=True)
                return f"No results from {tool_name}"
            formatted = f"Results from {tool_name}:\n" + "\n".join(str(item) for item in tool_result[:5])
            logger.observe("format_result", tool=tool_name, success=True, count=len(tool_result))
            return formatted
        
        # Fallback
        formatted = str(tool_result)
        logger.observe("format_result", tool=tool_name, success=True, type="fallback")
        return formatted
    
    @traceable()
    def _format_by_tool(self, result: dict, tool_name: str) -> str:
        """
        Route to tool-specific formatting function.
        
        Args:
            result: Tool result dictionary
            tool_name: Name of the tool
            
        Returns:
            str: Formatted result
        """
        # Skill evaluator
        if tool_name == 'skill_evaluator':
            return self._format_skill_evaluation(result)
        
        # Web search tools
        if tool_name in ('web_search', 'tavily_search'):
            return self._format_web_search(result)
        
        # Life event tool
        if tool_name == 'life_event':
            return self._format_life_event(result)
        
        # User preference tool
        if tool_name == 'user_preference':
            return self._format_user_preference(result)
        
        # Clarify communication tool - EMPATHY COACHING
        if tool_name == 'clarify_communication':
            return self._format_clarify_communication(result)
        
        # Generic data field handling
        if 'data' in result:
            return self._format_data(result['data'], tool_name)
        
        # Status/message format
        if 'status' in result and 'message' in result:
            formatted = f"[{result['status'].upper()}] {result['message']}"
            
            # Add additional info if present
            if 'count' in result:
                formatted += f"\nCount: {result['count']}"
            if 'total' in result:
                formatted += f"\nTotal: {result['total']}"
            
            return formatted
        
        # Fallback: nicely formatted dict
        return self._format_dict(result, tool_name)
    
    def _format_skill_evaluation(self, result: dict) -> str:
        """
        Format skill evaluation results with emojis and structure.
        
        Args:
            result: Skill evaluation result dictionary
            
        Returns:
            str: Formatted skill evaluation
        """
        parts = []
        
        # Status and message
        if result.get('message'):
            parts.append(result['message'])
        
        # Skills updated/demonstrated
        if result.get('skills_updated'):
            skills_updated = result['skills_updated']
            if isinstance(skills_updated, list) and skills_updated:
                parts.append("\n🎯 Skills Demonstrated:")
                for update in skills_updated[:5]:
                    if isinstance(update, dict):
                        skill = update.get('skill', 'Unknown')
                        old = update.get('old_level', 0)
                        new = update.get('new_level', 0)
                        improved = update.get('improved', False)
                        
                        if improved:
                            parts.append(f"  ✅ {skill}: {old} → {new} (Improved!)")
                        else:
                            parts.append(f"  • {skill}: {new}/10 (Max reached)")
        
        # Current skills
        if result.get('current_skills'):
            parts.append("\n📊 Overall Skill Levels:")
            skills = result['current_skills']
            
            if isinstance(skills, dict):
                for skill, score in skills.items():
                    parts.append(f"  • {skill}: {score}/100")
            elif isinstance(skills, list):
                for skill_obj in skills[:5]:
                    if isinstance(skill_obj, dict):
                        name = skill_obj.get('skill', skill_obj.get('name', 'Unknown'))
                        level = skill_obj.get('current_level', skill_obj.get('score', 0))
                        feedback = skill_obj.get('feedback', '')
                        parts.append(f"  • {name}: {level}/10 {feedback}")
        
        # Message analysis
        if result.get('message_analysis'):
            analysis = result['message_analysis']
            if isinstance(analysis, dict):
                detected = analysis.get('detected_skills', [])
                if detected:
                    skill_names = []
                    for item in detected:
                        if isinstance(item, dict):
                            skill_names.append(item.get('skill', 'Unknown'))
                        else:
                            skill_names.append(str(item))
                    if skill_names:
                        parts.append(f"\n✨ Detected in your message: {', '.join(skill_names)}")
        
        # Suggestions
        if result.get('suggestions'):
            parts.append("\n💡 Suggestions:")
            suggestions = result['suggestions']
            if isinstance(suggestions, list):
                for suggestion in suggestions[:3]:
                    if isinstance(suggestion, dict):
                        text = suggestion.get('text') or suggestion.get('suggestion', str(suggestion))
                    else:
                        text = str(suggestion)
                    parts.append(f"  • {text}")
        
        # Research info
        if result.get('latest_standards'):
            parts.append("\n🔬 Evaluated using latest social skills research")
        
        return "\n".join(parts) if parts else self._format_dict(result, 'skill_evaluator')
    
    def _format_web_search(self, result: dict) -> str:
        """
        Format web search results concisely.
        
        Args:
            result: Web search result dictionary
            
        Returns:
            str: Formatted search results
        """
        query = result.get('query', 'search')
        results_count = result.get('results_count', 0)
        data = result.get('data', [])
        
        if not data:
            return f"No results found for '{query}'"
        
        # List of results
        if isinstance(data, list):
            parts = [f"🔍 Found {results_count} results for '{query}':"]
            
            for i, item in enumerate(data[:3], 1):
                if isinstance(item, dict):
                    title = item.get('title', item.get('name', 'Result'))
                    content = item.get('content', item.get('snippet', item.get('description', '')))
                    
                    parts.append(f"\n{i}. {title}")
                    if content:
                        if len(content) > 500:
                            content = content[:500] + "..."
                        parts.append(f"   {content}")
                elif isinstance(item, str):
                    parts.append(f"\n{i}. {item[:150]}...")
            
            if len(data) > 3:
                parts.append(f"\n... and {len(data) - 3} more results")
            
            return "\n".join(parts)
        
        # Dict or string data
        elif isinstance(data, dict):
            return f"🔍 Search results for '{query}':\n" + self._format_dict(data, 'web_search')
        else:
            return f"🔍 Search result for '{query}': {str(data)[:200]}"
    
    def _format_life_event(self, result: dict) -> str:
        """Format life event tool results."""
        if result.get('status') == 'success':
            if 'event' in result:
                event = result['event']
                return f"Event: {event.get('title', 'Untitled')}\n{result.get('message', '')}"
            elif 'events' in result:
                count = result.get('count', len(result.get('events', [])))
                return f"Found {count} events\n{result.get('message', '')}"
            elif 'timeline' in result:
                return f"Timeline generated\n{result.get('message', '')}"
        
        return self._format_dict(result, 'life_event')
    
    def _format_user_preference(self, result: dict) -> str:
        """Format user preference tool results."""
        if result.get('status') == 'success':
            if 'preferences' in result:
                prefs = result['preferences']
                total = result.get('total', len(prefs))
                return f"Retrieved {total} preferences\n{result.get('message', '')}"
        
        return self._format_dict(result, 'user_preference')
    
    def _format_clarify_communication(self, result: dict) -> str:
        """
        Format clarify_communication results with clear empathy coaching instructions.
        
        This format is designed to be clear for local LLMs to understand and act on.
        """
        parts = []
        
        # Check if empathy issue was detected
        is_problematic = result.get('EMPATHY_ISSUE_DETECTED', False)
        original_text = result.get('original_text', '')
        coaching = result.get('coaching_analysis', '')
        action = result.get('action_required', 'NONE')
        
        if is_problematic:
            parts.append("⚠️ EMPATHY COACHING REQUIRED!")
            parts.append(f"\n📝 Original message: \"{original_text}\"")
            parts.append(f"\n🚨 Action: {action}")
            parts.append(f"\n📖 Coaching analysis:\n{coaching}")
            parts.append("\n\n⛔ YOUR TASK: Explain why this message is hurtful and suggest a better way to communicate!")
        else:
            parts.append("✅ Message analyzed - no major issues detected")
            if coaching:
                parts.append(f"\n📖 Analysis:\n{coaching}")
        
        return "\n".join(parts)
    
    def _format_data(self, data: Any, tool_name: str) -> str:
        """
        Format generic data field.
        
        Args:
            data: Data to format
            tool_name: Tool name
            
        Returns:
            str: Formatted data
        """
        if isinstance(data, dict):
            key_info = []
            for key, value in list(data.items())[:5]:
                key_info.append(f"- {key}: {value}")
            return f"Results from {tool_name}:\n" + "\n".join(key_info)
        
        return str(data)
    
    def _format_dict(self, data: dict, tool_name: str) -> str:
        """
        Format a dictionary in a readable way.
        
        Args:
            data: Dictionary to format
            tool_name: Tool name
            
        Returns:
            str: Formatted dictionary
        """
        if not data:
            return f"No data from {tool_name}"
        
        parts = [f"Results from {tool_name}:"]
        
        for key, value in list(data.items())[:5]:
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            parts.append(f"  • {key}: {value_str}")
        
        if len(data) > 5:
            parts.append(f"  ... and {len(data) - 5} more fields")
        
        return "\n".join(parts)
    
    @traceable()
    @observe("generate_fallback")
    def generate_fallback(
        self,
        tool_result: Optional[Any] = None,
        tool_name: Optional[str] = None
    ) -> AIMessage:
        """
        Generate a fallback response when LLM returns empty content.
        
        TRACE PATH:
            FALLBACK → Check tool result → Format → Create AIMessage
        
        Args:
            tool_result: The tool result to use in fallback (optional)
            tool_name: Name of the tool that was called (optional)
            
        Returns:
            AIMessage: A fallback message with content
        """
        logger.trace("FALLBACK", f"Generating fallback, has_tool_result={bool(tool_result)}")
        
        if tool_result and tool_name:
            formatted = self.format_tool_result(tool_result, tool_name)
            content = f"Based on the {tool_name} results:\n\n{formatted}"
            logger.observe("fallback_generated", has_tool_result=True, tool=tool_name)
        elif tool_result:
            content = f"Based on the information I found:\n\n{str(tool_result)[:500]}"
            logger.observe("fallback_generated", has_tool_result=True, tool="unknown")
        else:
            content = (
                "I apologize, but I'm having trouble generating a response. "
                "Could you please rephrase your question or try asking something else?"
            )
            logger.observe("fallback_generated", has_tool_result=False)
        
        return AIMessage(content=content)
    
    @traceable()
    @observe("extract_tool_result")
    def extract_tool_result_from_messages(
        self,
        messages: List,
        look_back: int = 3
    ) -> Optional[Tuple[Any, str]]:
        """
        Extract the most recent tool result from message history.
        
        TRACE PATH:
            EXTRACT_TOOL → Search messages → Find ToolMessage
        
        Args:
            messages: List of messages to search
            look_back: How many messages to look back
            
        Returns:
            Optional[Tuple[Any, str]]: (tool_result, tool_name) if found, None otherwise
        """
        logger.trace("EXTRACT_TOOL", f"Searching last {look_back} messages")
        
        # Look at recent messages in reverse order
        for i, msg in enumerate(reversed(messages[-look_back:])):
            # Check if it's a ToolMessage
            if hasattr(msg, 'type') and msg.type == 'tool':
                tool_result = msg.content
                tool_name = getattr(msg, 'name', 'unknown_tool')
                logger.observe("tool_result_found", tool=tool_name, position=i)
                return (tool_result, tool_name)
            
            # Check if it has tool_calls
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown_tool')
                    logger.observe("tool_call_found", tool=tool_name, position=i)
                    return (None, tool_name)
        
        logger.observe("tool_result_found", found=False)
        return None
    
    @observe("create_fallback_response")
    def create_response_with_fallback(
        self,
        response: AIMessage,
        messages: List
    ) -> AIMessage:
        """
        Check if response is empty and create fallback if needed.
        
        TRACE PATH:
            CHECK_EMPTY → Extract tool → Generate fallback
        
        Args:
            response: The AI response to check
            messages: Message history for extracting tool results
            
        Returns:
            AIMessage: Original response if valid, fallback otherwise
        """
        if not self.is_empty_response(response):
            logger.observe("fallback_needed", needed=False)
            return response
        
        logger.trace("FALLBACK", "Empty response detected, generating fallback")
        logger.observe("fallback_needed", needed=True)
        
        # Try to find tool results in recent messages
        tool_info = self.extract_tool_result_from_messages(messages)
        
        if tool_info:
            tool_result, tool_name = tool_info
            if tool_result:
                logger.info(f"✅ Found tool result from {tool_name}, generating response")
                return self.generate_fallback(tool_result, tool_name)
        
        # No tool results found, generic fallback
        logger.warning("⚠️  No tool results found, using generic fallback")
        return self.generate_fallback()
    
    @traceable()
    def extract_model_name(self, response: Any) -> str:
        """
        Extract the model name from a response.
        
        TRACE PATH:
            MODEL_DETECT → Check response_metadata → Extract model
        
        Args:
            response: The AI response
            
        Returns:
            str: Model name or "unknown"
        """
        logger.trace("MODEL_DETECT", "Extracting model name from response")
        
        try:
            # Check response_metadata
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                if isinstance(metadata, dict):
                    # OpenAI format
                    if 'model' in metadata:
                        model = metadata['model']
                        logger.observe("model_detected", model=model, provider="openai")
                        return model
                    # Anthropic format
                    if 'model_name' in metadata:
                        model = metadata['model_name']
                        logger.observe("model_detected", model=model, provider="anthropic")
                        return model
            
            # Check direct model attribute
            if hasattr(response, 'model'):
                model = response.model
                logger.observe("model_detected", model=model, provider="direct")
                return model
            
            logger.observe("model_detected", model="unknown")
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error extracting model name: {e}")
            logger.observe("model_detected", model="error", error=str(e))
            return "unknown"
