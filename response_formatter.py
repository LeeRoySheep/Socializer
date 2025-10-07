"""
Response Formatter - Makes AI tool outputs human-readable
Converts raw JSON/dict responses into natural, conversational text
"""

from typing import Any, Dict
import json


class ResponseFormatter:
    """Formats various tool outputs into human-readable text."""
    
    @staticmethod
    def format_weather(data: Dict[str, Any]) -> str:
        """Format weather data into readable text.
        
        Args:
            data: Weather API response dict
            
        Returns:
            Human-readable weather description
        """
        try:
            if not isinstance(data, dict):
                return str(data)
            
            location = data.get('location', {})
            current = data.get('current', {})
            
            if not location or not current:
                return str(data)
            
            # Extract location info
            city = location.get('name', 'Unknown location')
            country = location.get('country', '')
            local_time = location.get('localtime', '')
            
            # Extract weather info
            condition = current.get('condition', {}).get('text', 'Unknown')
            temp_c = current.get('temp_c')
            temp_f = current.get('temp_f')
            feels_like_c = current.get('feelslike_c')
            feels_like_f = current.get('feelslike_f')
            humidity = current.get('humidity')
            wind_kph = current.get('wind_kph')
            wind_mph = current.get('wind_mph')
            wind_dir = current.get('wind_dir', '')
            
            # Build readable response
            response = f"🌤️ **Current Weather in {city}"
            if country:
                response += f", {country}"
            response += "**\n\n"
            
            # Condition
            response += f"**Condition:** {condition}\n"
            
            # Temperature
            if temp_c is not None:
                response += f"**Temperature:** {temp_c}°C ({temp_f}°F)\n"
                if feels_like_c is not None and abs(feels_like_c - temp_c) > 2:
                    response += f"**Feels like:** {feels_like_c}°C ({feels_like_f}°F)\n"
            
            # Humidity
            if humidity is not None:
                response += f"**Humidity:** {humidity}%\n"
            
            # Wind
            if wind_kph is not None:
                response += f"**Wind:** {wind_dir} at {wind_kph} km/h ({wind_mph} mph)\n"
            
            # Local time
            if local_time:
                response += f"\n*Local time: {local_time}*"
            
            return response
            
        except Exception as e:
            print(f"Error formatting weather: {e}")
            return str(data)
    
    @staticmethod
    def format_search_results(data: Any) -> str:
        """Format web search results into readable text.
        
        Args:
            data: Search results (string or dict)
            
        Returns:
            Human-readable search summary
        """
        try:
            if isinstance(data, str):
                # Already formatted or simple text
                return data
            
            if isinstance(data, dict):
                # Check if it's a list of search results
                if 'results' in data:
                    results = data['results']
                    if not results:
                        return "I couldn't find any relevant information."
                    
                    response = "📚 **Search Results:**\n\n"
                    for i, result in enumerate(results[:3], 1):  # Top 3 results
                        title = result.get('title', 'No title')
                        content = result.get('content', result.get('snippet', ''))
                        url = result.get('url', '')
                        
                        response += f"**{i}. {title}**\n"
                        if content:
                            # Limit content length
                            content = content[:200] + "..." if len(content) > 200 else content
                            response += f"{content}\n"
                        if url:
                            response += f"*Source: {url}*\n"
                        response += "\n"
                    
                    return response
                
                # Generic dict formatting
                return json.dumps(data, indent=2)
            
            return str(data)
            
        except Exception as e:
            print(f"Error formatting search results: {e}")
            return str(data)
    
    @staticmethod
    def format_conversation_history(data: Any) -> str:
        """Format conversation history into readable text.
        
        Args:
            data: Conversation history (string or dict)
            
        Returns:
            Human-readable conversation summary
        """
        try:
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    return data
            
            if isinstance(data, dict):
                messages = data.get('data', [])
                
                if not messages:
                    return "No previous conversation found."
                
                response = "💬 **Previous Conversation:**\n\n"
                for msg in messages[-5:]:  # Last 5 messages
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    
                    if role == 'user':
                        response += f"**You:** {content}\n"
                    elif role == 'assistant':
                        response += f"**AI:** {content}\n"
                    else:
                        response += f"**{role.title()}:** {content}\n"
                    response += "\n"
                
                return response
            
            return str(data)
            
        except Exception as e:
            print(f"Error formatting conversation history: {e}")
            return str(data)
    
    @staticmethod
    def format_tool_result(tool_name: str, result: Any) -> str:
        """Format any tool result based on tool type.
        
        Args:
            tool_name: Name of the tool that was used
            result: Raw result from the tool
            
        Returns:
            Human-readable formatted result
        """
        try:
            # Handle different tool types
            if tool_name == 'tavily_search' or 'search' in tool_name.lower():
                # Check if it's weather data
                if isinstance(result, dict) and 'location' in result and 'current' in result:
                    return ResponseFormatter.format_weather(result)
                else:
                    return ResponseFormatter.format_search_results(result)
            
            elif tool_name == 'recall_last_conversation' or 'conversation' in tool_name.lower():
                return ResponseFormatter.format_conversation_history(result)
            
            elif tool_name == 'skill_evaluator':
                if isinstance(result, dict):
                    skill_name = result.get('skill', 'Unknown')
                    level = result.get('level', 'Unknown')
                    feedback = result.get('feedback', '')
                    
                    response = f"📊 **Skill Evaluation: {skill_name}**\n\n"
                    response += f"**Level:** {level}\n"
                    if feedback:
                        response += f"**Feedback:** {feedback}\n"
                    
                    return response
            
            elif tool_name == 'life_event':
                if isinstance(result, dict):
                    status = result.get('status', '')
                    message = result.get('message', '')
                    data = result.get('data', {})
                    
                    if status == 'success':
                        if isinstance(data, list):
                            response = "📅 **Life Events:**\n\n"
                            for event in data:
                                title = event.get('title', 'Untitled')
                                date = event.get('date', '')
                                response += f"• **{title}** - {date}\n"
                            return response
                        else:
                            return message or str(data)
                    else:
                        return message or str(result)
            
            # Default: try to make it readable
            if isinstance(result, dict):
                # Pretty print JSON
                return json.dumps(result, indent=2)
            
            return str(result)
            
        except Exception as e:
            print(f"Error formatting tool result: {e}")
            return str(result)
    
    @staticmethod
    def clean_response(text: str) -> str:
        """Clean up response text for better readability.
        
        Args:
            text: Raw response text
            
        Returns:
            Cleaned up text
        """
        # Remove excessive newlines
        while '\n\n\n' in text:
            text = text.replace('\n\n\n', '\n\n')
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text


# Convenience function for easy import
def format_tool_result(tool_name: str, result: Any) -> str:
    """Convenience wrapper for ResponseFormatter.format_tool_result"""
    return ResponseFormatter.format_tool_result(tool_name, result)


def format_weather(data: Dict[str, Any]) -> str:
    """Convenience wrapper for ResponseFormatter.format_weather"""
    return ResponseFormatter.format_weather(data)
