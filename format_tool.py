"""Format Tool - Makes raw data human-readable."""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Any, Dict
from response_formatter import ResponseFormatter
import json


class FormatInput(BaseModel):
    """Input for the format tool."""
    data: str = Field(description="The raw data (JSON, dict, or string) to format into human-readable text")
    data_type: str = Field(
        default="auto",
        description="Type of data: 'weather', 'search', 'conversation', 'auto' (default)"
    )


class FormatTool(BaseTool):
    """Tool for formatting raw data into human-readable text.
    
    Use this when you receive raw JSON or dictionary data that needs to be
    presented to users in a friendly, conversational format.
    """
    
    name: str = "format_output"
    description: str = (
        "Format raw data (JSON, dictionaries, API responses) into beautiful, "
        "human-readable text with emojis and proper structure. "
        "Use this ALWAYS when you receive raw data from other tools. "
        "Input: raw data string. Output: formatted, conversational text."
    )
    args_schema: Type[BaseModel] = FormatInput
    
    def _run(self, data: str, data_type: str = "auto") -> str:
        """Format the data into human-readable text.
        
        Args:
            data: Raw data string (JSON or dict format)
            data_type: Type of data ('weather', 'search', 'conversation', 'auto')
            
        Returns:
            Formatted, human-readable text
        """
        try:
            # Try to parse as JSON if it's a string
            if isinstance(data, str):
                try:
                    parsed_data = json.loads(data)
                except:
                    # Not JSON, might be already formatted
                    if '{' not in data and 'location' not in data.lower():
                        # Already looks human-readable
                        return data
                    parsed_data = data
            else:
                parsed_data = data
            
            # Auto-detect data type if not specified
            if data_type == "auto":
                if isinstance(parsed_data, dict):
                    if 'location' in parsed_data and 'current' in parsed_data:
                        data_type = "weather"
                    elif 'results' in parsed_data:
                        data_type = "search"
                    elif 'data' in parsed_data and isinstance(parsed_data.get('data'), list):
                        data_type = "conversation"
            
            # Format based on type
            if data_type == "weather":
                return ResponseFormatter.format_weather(parsed_data)
            elif data_type == "search":
                return ResponseFormatter.format_search_results(parsed_data)
            elif data_type == "conversation":
                return ResponseFormatter.format_conversation_history(parsed_data)
            else:
                # Generic formatting
                if isinstance(parsed_data, dict) and 'location' in parsed_data:
                    return ResponseFormatter.format_weather(parsed_data)
                return ResponseFormatter.format_tool_result("generic", parsed_data)
                
        except Exception as e:
            # If formatting fails, return a cleaned version
            return f"Here's the information: {str(data)[:500]}"
    
    async def _arun(self, data: str, data_type: str = "auto") -> str:
        """Async version."""
        return self._run(data, data_type)
