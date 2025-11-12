"""
Tavily Search Tool with OTE Compliance

LOCATION: tools/search/tavily_search_tool.py
PURPOSE: Web search wrapper with OTE tracking for real-time information retrieval

TRACE POINTS:
    - VALIDATE: Input validation
    - SEARCH: Search execution
    - FORMAT: Result formatting
    
DEPENDENCIES:
    - langchain_tavily.TavilySearch
    
OTE COMPLIANCE:
    - Observability: All searches logged with timing
    - Traceability: Trace markers for search flow
    - Evaluation: Search performance and result metrics
"""

from typing import Type, Any, Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.utils import get_logger, observe, traceable

# Get logger for this module
logger = get_logger(__name__)


class TavilySearchInput(BaseModel):
    """
    Input schema for TavilySearchTool.
    
    Attributes:
        query: The search query string
    """
    query: str = Field(description="The search query string")


class TavilySearchTool(BaseTool):
    """
    Web search tool wrapper with OTE tracking.
    
    This tool provides web search capabilities for finding current information,
    news, weather, and other real-time data. All searches are logged and timed
    for performance monitoring.
    
    OTE Compliance:
        - All searches observed with timing
        - Trace markers show search flow
        - Result size and format tracked
        - Error rates monitored
    
    Attributes:
        name: Tool name for LLM
        description: Tool description for LLM
        args_schema: Pydantic schema for validation
        search_tool: Underlying search tool (TavilySearch)
    
    Example:
        >>> from langchain_tavily import TavilySearch
        >>> tavily = TavilySearch(max_results=10)
        >>> tool = TavilySearchTool(search_tool=tavily)
        >>> result = tool.run("current weather in Paris")
        >>> print(result)
        Current weather in Paris: ...
    """
    
    name: str = "tavily_search"
    description: str = """Search the web for current information.
    
    Use this tool when you need to find up-to-date information, current events, 
    or real-time data like time, weather, news, etc.
    
    Input: A search query string (e.g. 'current weather in Paris', 'latest news')
    """
    args_schema: Type[BaseModel] = TavilySearchInput
    search_tool: Any = None  # TavilySearch instance
    
    def __init__(self, search_tool, **data):
        """
        Initialize TavilySearchTool.
        
        Args:
            search_tool: TavilySearch instance for performing searches
            **data: Additional Pydantic model data
        """
        # Initialize BaseTool first
        super().__init__(**data)
        # Set search tool (Pydantic workaround)
        object.__setattr__(self, 'search_tool', search_tool)
        
        logger.trace("INIT", "TavilySearchTool initialized")
        logger.observe("init_complete", has_search_tool=bool(search_tool))
    
    @observe("tavily_search")
    def _run(self, query: str, **kwargs) -> str:
        """
        Execute search synchronously with OTE tracking.
        
        TRACE PATH:
            VALIDATE → SEARCH → FORMAT
        
        Args:
            query: Search query string or dict with 'query' key
            **kwargs: Additional arguments (unused)
            
        Returns:
            Formatted search results as string
        """
        return self._execute_search(query)
    
    async def _arun(self, query: str, **kwargs) -> str:
        """
        Execute search asynchronously.
        
        Note:
            Currently calls sync version. Can be optimized for async operations.
        
        Args:
            query: Search query string
            **kwargs: Additional arguments
            
        Returns:
            Formatted search results
        """
        return self._execute_search(query)
    
    @traceable()
    @observe("execute_search")
    def _execute_search(self, query: Any) -> str:
        """
        Execute search and return formatted results with OTE tracking.
        
        TRACE PATH:
            1. VALIDATE → Input validation
            2. SEARCH → Execute search API call
            3. FORMAT → Format results based on type
        
        Args:
            query: Search query (string or dict)
            
        Returns:
            Formatted search results, limited to 2000 chars
        """
        try:
            # TRACE POINT 1: Validation
            logger.trace("VALIDATE", f"Validating search query: {type(query)}")
            
            if not query:
                logger.warning("Empty query provided")
                return "No search query provided."
            
            # Handle both string and dict queries
            search_query = query.get('query', '') if isinstance(query, dict) else str(query)
            if not search_query.strip():
                logger.warning("Empty search query after processing")
                return "Empty search query provided."
            
            # TRACE POINT 2: Search execution
            logger.trace("SEARCH", f"Executing search: {search_query[:100]}")
            result = self.search_tool.invoke(search_query)
            
            # TRACE POINT 3: Format results
            logger.trace("FORMAT", f"Formatting result type: {type(result)}")
            formatted_result = self._format_result(result)
            
            logger.observe(
                "search_complete",
                query_length=len(search_query),
                result_length=len(formatted_result),
                success=True
            )
            
            return formatted_result
            
        except Exception as e:
            logger.error(f"Error in Tavily search: {str(e)}", exc_info=True)
            logger.observe("search_complete", success=False, error=str(e))
            return f"I encountered an error while searching: {str(e)}"
    
    @traceable()
    def _format_result(self, result: Any) -> str:
        """
        Format search results based on result type.
        
        Handles:
        - String results (return as-is, truncated)
        - Weather API responses (formatted)
        - Tavily search results (extract top result)
        - Other dict formats (stringify)
        
        Args:
            result: Raw search result from API
            
        Returns:
            Formatted string result, max 2000 chars
        """
        logger.trace("FORMAT", f"Formatting result of type: {type(result)}")
        
        # No results
        if not result:
            logger.warning("No results found")
            return "No results found."
        
        # String result
        if isinstance(result, str):
            logger.trace("FORMAT", "Result is string, truncating")
            return result[:2000]
        
        # Dict result
        if isinstance(result, dict):
            # Weather API format
            if 'current' in result and 'condition' in result['current']:
                logger.trace("FORMAT", "Detected weather API format")
                return self._format_weather(result)
            
            # Tavily search results
            if 'results' in result and result['results']:
                logger.trace("FORMAT", "Detected Tavily search format")
                return self._format_tavily_results(result)
            
            # Generic dict
            logger.trace("FORMAT", "Generic dict format")
            return str(result)[:2000]
        
        # Other types
        logger.trace("FORMAT", "Fallback to string conversion")
        return str(result)[:2000]
    
    def _format_weather(self, result: Dict) -> str:
        """
        Format weather API response.
        
        Args:
            result: Weather API response dict
            
        Returns:
            Human-readable weather string
        """
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
    
    def _format_tavily_results(self, result: Dict) -> str:
        """
        Format Tavily search results.
        
        Extracts the top result's content or description.
        
        Args:
            result: Tavily search response dict
            
        Returns:
            Top result content
        """
        top_result = result['results'][0]
        content = top_result.get('content') or top_result.get('description', 'No content available')
        logger.trace("FORMAT", f"Extracted Tavily result, length={len(content)}")
        return content
    
    @observe("search_invoke")
    def invoke(self, input_data: Any) -> str:
        """
        Handle tool invocation with flexible input format.
        
        Supports both string queries and dict with 'query' key.
        
        Args:
            input_data: Search query (string or dict)
            
        Returns:
            Search results or error message
        """
        logger.trace("INVOKE", f"Tool invoked with type: {type(input_data)}")
        
        try:
            if isinstance(input_data, dict) and 'query' in input_data:
                return self._execute_search(input_data['query'])
            elif isinstance(input_data, str):
                return self._execute_search(input_data)
            else:
                logger.warning(f"Invalid input format: {type(input_data)}")
                return "Error: Invalid input format. Please provide a search query or a dictionary with a 'query' key."
        except Exception as e:
            logger.error(f"Error in invoke: {str(e)}", exc_info=True)
            return f"Error performing search: {str(e)}"
