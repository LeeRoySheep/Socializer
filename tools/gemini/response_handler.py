"""
GeminiResponseHandler - Handle Gemini Tool Responses
=====================================================

This module handles tool responses from Gemini to ensure proper formatting
and prevent empty responses.

Author: AI Assistant
Date: 2025-10-22
"""

from typing import Any, Dict, Optional
from langchain_core.messages import AIMessage, ToolMessage


class GeminiResponseHandler:
    """
    Handles tool responses from Gemini and ensures proper formatting.
    
    Problem It Solves:
    -------------------
    Gemini sometimes returns empty responses after tool calls.
    This handler:
    1. Detects empty responses
    2. Formats tool results properly
    3. Generates fallback responses when needed
    
    Usage:
    ------
    ```python
    handler = GeminiResponseHandler()
    
    # Check if response is empty
    if handler.is_empty_response(ai_message):
        # Generate fallback
        fallback = handler.generate_fallback(tool_result)
    ```
    """
    
    # Patterns that indicate an empty response
    EMPTY_PATTERNS = {'', '```', '\n```', '`', '\n', ' '}
    
    def __init__(self):
        """Initialize the response handler."""
        pass
    
    def is_empty_response(self, response: AIMessage) -> bool:
        """
        Check if an AI response is effectively empty.
        
        Parameters:
        -----------
        response : AIMessage
            The AI message to check
        
        Returns:
        --------
        bool
            True if response is empty, False otherwise
        """
        if not response:
            return True
        
        content = self._extract_content(response)
        
        if not content:
            return True
        
        # Check against empty patterns
        if content.strip() in self.EMPTY_PATTERNS:
            return True
        
        # Check if it's just whitespace
        if not content.strip():
            return True
        
        return False
    
    def _extract_content(self, message: Any) -> str:
        """
        Extract text content from a message.
        
        Parameters:
        -----------
        message : Any
            The message object
        
        Returns:
        --------
        str
            The extracted content
        """
        if hasattr(message, 'content'):
            return str(message.content)
        elif isinstance(message, dict):
            return str(message.get('content', ''))
        else:
            return str(message)
    
    def format_tool_result(self, tool_result: Any, tool_name: str) -> str:
        """
        Format a tool result into a human-readable string.
        
        Parameters:
        -----------
        tool_result : Any
            The result from the tool
        tool_name : str
            Name of the tool that produced the result
        
        Returns:
        --------
        str
            Formatted result string
        """
        # Handle dictionary results
        if isinstance(tool_result, dict):
            # Error handling
            if 'error' in tool_result:
                return f"Error from {tool_name}: {tool_result.get('error', 'Unknown error')}"
            
            # ✅ Special handling for specific tools (BEFORE generic data check)
            if tool_name == 'skill_evaluator':
                return self._format_skill_evaluation(tool_result)
            
            if tool_name == 'web_search':
                return self._format_web_search(tool_result)
            
            # Generic data field handling (for tools without special formatting)
            if 'data' in tool_result:
                return self._format_data(tool_result['data'], tool_name)
            
            # ✅ For other dicts with status/message, extract key info
            if 'status' in tool_result and 'message' in tool_result:
                formatted = f"[{tool_result['status'].upper()}] {tool_result['message']}"
                
                # Add any scores or suggestions if present
                if 'skill_scores' in tool_result:
                    formatted += f"\n\nSkill Scores: {tool_result['skill_scores']}"
                if 'suggestions' in tool_result and tool_result['suggestions']:
                    formatted += f"\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in tool_result['suggestions'][:3])
                
                return formatted
            
            # ✅ Fallback: Format dict nicely, not as raw string
            return self._format_dict(tool_result, tool_name)
        
        # Handle string results
        if isinstance(tool_result, str):
            return tool_result
        
        # Handle list results
        if isinstance(tool_result, list):
            if not tool_result:
                return f"No results from {tool_name}"
            return f"Results from {tool_name}:\n" + "\n".join(str(item) for item in tool_result[:5])
        
        # Fallback
        return str(tool_result)
    
    def _format_data(self, data: Any, tool_name: str) -> str:
        """
        Format the data portion of a tool result.
        
        Parameters:
        -----------
        data : Any
            The data to format
        tool_name : str
            Name of the tool
        
        Returns:
        --------
        str
            Formatted data string
        """
        if isinstance(data, dict):
            # Format key information from dictionary
            key_info = []
            for key, value in list(data.items())[:5]:  # Limit to first 5 items
                key_info.append(f"- {key}: {value}")
            return f"Results from {tool_name}:\n" + "\n".join(key_info)
        
        return str(data)
    
    def generate_fallback(
        self, 
        tool_result: Optional[Any] = None, 
        tool_name: Optional[str] = None
    ) -> AIMessage:
        """
        Generate a fallback response when Gemini returns empty content.
        
        Parameters:
        -----------
        tool_result : Optional[Any]
            The tool result to use in the fallback
        tool_name : Optional[str]
            Name of the tool that was called
        
        Returns:
        --------
        AIMessage
            A fallback message with content
        """
        if tool_result and tool_name:
            formatted = self.format_tool_result(tool_result, tool_name)
            content = f"Based on the {tool_name} results:\n\n{formatted}"
        elif tool_result:
            content = f"Based on the information I found:\n\n{str(tool_result)[:500]}"
        else:
            content = (
                "I apologize, but I'm having trouble generating a response. "
                "Could you please rephrase your question or try asking something else?"
            )
        
        return AIMessage(content=content)
    
    def extract_tool_result_from_messages(
        self, 
        messages: list, 
        look_back: int = 3
    ) -> Optional[tuple[Any, str]]:
        """
        Extract the most recent tool result from a message history.
        
        Parameters:
        -----------
        messages : list
            List of messages to search
        look_back : int
            How many messages to look back
        
        Returns:
        --------
        Optional[tuple[Any, str]]
            (tool_result, tool_name) if found, None otherwise
        """
        # Look at recent messages in reverse order
        for msg in reversed(messages[-look_back:]):
            # Check if it's a ToolMessage
            if hasattr(msg, 'type') and msg.type == 'tool':
                tool_result = msg.content
                tool_name = getattr(msg, 'name', 'unknown_tool')
                return (tool_result, tool_name)
            
            # Check if it has tool_calls
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    tool_name = tool_call.get('name') if isinstance(tool_call, dict) else getattr(tool_call, 'name', 'unknown_tool')
                    # Look for the corresponding result in next messages
                    return (None, tool_name)
        
        return None
    
    def _format_skill_evaluation(self, result: dict) -> str:
        """Format skill evaluation results in a clean, readable way."""
        parts = []
        
        # Status and message
        if result.get('message'):
            parts.append(result['message'])
        
        # ✅ NEW: Show which skills were updated/improved
        if result.get('skills_updated'):
            skills_updated = result['skills_updated']
            if isinstance(skills_updated, list) and skills_updated:
                parts.append("\n🎯 Skills Demonstrated:")
                for update in skills_updated[:5]:  # Show top 5
                    if isinstance(update, dict):
                        skill = update.get('skill', 'Unknown')
                        old = update.get('old_level', 0)
                        new = update.get('new_level', 0)
                        improved = update.get('improved', False)
                        
                        if improved:
                            parts.append(f"  ✅ {skill}: {old} → {new} (Improved!)")
                        else:
                            parts.append(f"  • {skill}: {new}/10 (Max reached)")
        
        # Current skills (handle both dict and list formats)
        if result.get('current_skills'):
            parts.append("\n📊 Overall Skill Levels:")
            skills = result['current_skills']
            
            if isinstance(skills, dict):
                for skill, score in skills.items():
                    parts.append(f"  • {skill}: {score}/100")
            elif isinstance(skills, list):
                for skill_obj in skills[:5]:  # Show top 5
                    if isinstance(skill_obj, dict):
                        name = skill_obj.get('skill', skill_obj.get('name', 'Unknown'))
                        level = skill_obj.get('current_level', skill_obj.get('score', 0))
                        feedback = skill_obj.get('feedback', '')
                        parts.append(f"  • {name}: {level}/10 {feedback}")
        
        # Message analysis (what was detected in this specific message)
        if result.get('message_analysis'):
            analysis = result['message_analysis']
            if isinstance(analysis, dict):
                detected = analysis.get('detected_skills', [])
                if detected:
                    parts.append(f"\n✨ Detected in your message: {', '.join(detected)}")
        
        # Suggestions (limit to 3 most important)
        if result.get('suggestions'):
            parts.append("\n💡 Suggestions:")
            suggestions = result['suggestions']
            if isinstance(suggestions, list):
                for suggestion in suggestions[:3]:
                    # Handle both string and dict suggestions
                    if isinstance(suggestion, dict):
                        text = suggestion.get('text') or suggestion.get('suggestion', str(suggestion))
                    else:
                        text = str(suggestion)
                    parts.append(f"  • {text}")
        
        # Research info (if available)
        if result.get('latest_standards'):
            research = result['latest_standards']
            if isinstance(research, dict):
                parts.append(f"\n🔬 Evaluated using latest social skills research")
        
        return "\n".join(parts) if parts else self._format_dict(result, 'skill_evaluator')
    
    def _format_web_search(self, result: dict) -> str:
        """Format web search results in a clean, concise way."""
        # Extract key information
        query = result.get('query', 'search')
        results_count = result.get('results_count', 0)
        data = result.get('data', [])
        
        # Simple format: just return the search results concisely
        if not data:
            return f"No results found for '{query}'"
        
        # If data is a list of results
        if isinstance(data, list):
            # Format as a simple summary (let LLM describe details)
            parts = [f"🔍 Found {results_count} results for '{query}':"]
            
            for i, item in enumerate(data[:3], 1):  # Show top 3
                if isinstance(item, dict):
                    title = item.get('title', item.get('name', 'Result'))
                    content = item.get('content', item.get('snippet', item.get('description', '')))
                    
                    # Truncate content
                    if content and len(content) > 150:
                        content = content[:150] + "..."
                    
                    parts.append(f"\n{i}. {title}")
                    if content:
                        parts.append(f"   {content}")
                elif isinstance(item, str):
                    # Just a string result
                    parts.append(f"\n{i}. {item[:150]}...")
            
            if len(data) > 3:
                parts.append(f"\n... and {len(data) - 3} more results")
            
            return "\n".join(parts)
        
        # If data is a dict or string, just return it nicely formatted
        elif isinstance(data, dict):
            return f"🔍 Search results for '{query}':\n" + self._format_dict(data, 'web_search')
        else:
            return f"🔍 Search result for '{query}': {str(data)[:200]}"
    
    def _format_dict(self, data: dict, tool_name: str) -> str:
        """Format a dictionary result in a readable way (not raw string dump)."""
        if not data:
            return f"No data from {tool_name}"
        
        parts = [f"Results from {tool_name}:"]
        
        # Limit to first 5 key-value pairs
        for key, value in list(data.items())[:5]:
            # Truncate long values
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            parts.append(f"  • {key}: {value_str}")
        
        if len(data) > 5:
            parts.append(f"  ... and {len(data) - 5} more fields")
        
        return "\n".join(parts)
    
    def create_response_with_fallback(
        self,
        response: AIMessage,
        messages: list
    ) -> AIMessage:
        """
        Check if response is empty and create fallback if needed.
        
        Parameters:
        -----------
        response : AIMessage
            The AI response to check
        messages : list
            Message history for extracting tool results
        
        Returns:
        --------
        AIMessage
            Original response if valid, fallback otherwise
        """
        if not self.is_empty_response(response):
            return response
        
        print("⚠️  Detected empty response - generating fallback")
        
        # Try to find tool results in recent messages
        tool_info = self.extract_tool_result_from_messages(messages)
        
        if tool_info:
            tool_result, tool_name = tool_info
            if tool_result:
                print(f"✅ Found tool result from {tool_name}, generating response")
                return self.generate_fallback(tool_result, tool_name)
        
        # No tool results found, generic fallback
        print("⚠️  No tool results found, using generic fallback")
        return self.generate_fallback()
