"""
Tavily Web Search Tool for the chat system.
Handles web searches with proper error handling and result formatting.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from langchain_core.tools import BaseTool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class SearchError(Exception):
    """Custom exception for search-related errors."""
    pass

class WebSearchTool(BaseTool):
    """Tool for performing web searches using Tavily API."""
    
    name: str = "web_search"
    description: str = """
    Useful for searching the web for current information.
    Input should be a search query.
    """
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize the Tavily search tool.
        
        Args:
            api_key: Optional Tavily API key. If not provided, will look for TAVILY_API_KEY in environment.
            **kwargs: Additional arguments to pass to the parent class.
        """
        super().__init__(**kwargs)
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")
        self.search_tool = None
        self._initialize_search_tool()
    
    def _initialize_search_tool(self):
        """Initialize the search tool with proper error handling."""
        if not self.api_key:
            raise SearchError(
                "Tavily API key not found. Please set the TAVILY_API_KEY environment variable "
                "or pass the api_key parameter when initializing WebSearchTool."
            )
        try:
            self.search_tool = TavilySearchResults(
                max_results=3,
                tavily_api_key=self.api_key
            )
        except Exception as e:
            raise SearchError(f"Failed to initialize search tool: {str(e)}")
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        """Format a single search result."""
        formatted = []
        if title := result.get('title'):
            formatted.append(f"Title: {title}")
        if url := result.get('url'):
            formatted.append(f"URL: {url}")
        if content := result.get('content'):
            formatted.append(f"Content: {content[:300]}{'...' if len(content) > 300 else ''}")
        return "\n".join(formatted)
    
    def _run(self, query: str) -> str:
        """Execute the search synchronously."""
        if not self.search_tool:
            return "Search functionality is not available. Please check your API key configuration."
            
        try:
            results = self.search_tool.invoke({"query": query})
            return self._format_search_results(results)
        except Exception as e:
            return f"Error performing search: {str(e)}"
    
    def _format_search_results(self, results: Dict[str, Any]) -> str:
        """Format search results into a readable string."""
        if not results or not results.get('results'):
            return "No results found for your search."
            
        formatted_results = [
            f"--- Result {i+1} ---\n{self._format_result(r)}"
            for i, r in enumerate(results['results'][:3])
        ]
        
        return "\n\n".join(["Search Results:", *formatted_results])
    
    async def _arun(self, query: str) -> str:
        """Execute the search asynchronously."""
        if not self.search_tool:
            return "Search functionality is not available. Please check your API key configuration."
            
        try:
            results = await self.search_tool.ainvoke({"query": query})
            return self._format_search_results(results)
        except Exception as e:
            return f"Error performing search: {str(e)}"

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test():
        search = WebSearchTool()
        
        # Test synchronous search
        print("=== Testing Synchronous Search ===")
        sync_result = search.run("current weather in Paris")
        print(sync_result)
        
        print("\n=== Testing Asynchronous Search ===")
        # Test asynchronous search
        async_result = await search.arun("latest tech news")
        print(async_result)
    
    asyncio.run(test())
