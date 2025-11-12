"""
Gemini-Compatible Web Search Tool
==================================

A web search tool built with GeminiToolBase for compatibility with Gemini API.

Uses Tavily API for web searches.

Author: AI Assistant
Date: 2025-10-22
"""

import os
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .base import GeminiToolBase

# Load environment variables
load_dotenv()


class SearchToolInput(BaseModel):
    """
    Input schema for SearchTool.
    
    Fully Gemini-compatible:
    - All fields have descriptions ✅
    - Optional field has default ✅
    - Simple types only ✅
    """
    query: str = Field(
        description="The search query string (e.g., 'current weather in Paris', 'latest AI news')"
    )
    max_results: Optional[int] = Field(
        default=5,
        description="Maximum number of search results to return (1-10)"
    )


class SearchTool(GeminiToolBase):
    """
    Web search tool using Tavily API.
    
    Features:
    ---------
    - Real-time web search
    - Weather information
    - News and current events
    - General knowledge queries
    
    Usage:
    ------
    ```python
    from tools.gemini.search_tool import SearchTool
    
    tool = SearchTool()
    result = tool._run(query="weather in Paris", max_results=3)
    print(result)
    ```
    
    Returns:
    --------
    Dict with:
    - status: 'success' or 'error'
    - message: Human-readable message
    - data: Search results (if successful)
    - query: Original query
    - results_count: Number of results
    """
    
    name: str = "web_search"
    description: str = (
        "Search the web for current information, real-time data, news, weather, "
        "and general knowledge. Use this when you need up-to-date information that "
        "you don't have in your knowledge base."
    )
    args_schema: Type[BaseModel] = SearchToolInput
    
    # Declare the tavily_client field for Pydantic
    tavily_client: Optional[Any] = None
    
    def __init__(self, **kwargs):
        """
        Initialize the SearchTool.
        
        Requires TAVILY_API_KEY in environment variables.
        """
        super().__init__(**kwargs)
        
        # Initialize Tavily search
        self._init_tavily()
    
    def _init_tavily(self):
        """Initialize Tavily search client."""
        api_key = os.getenv('TAVILY_API_KEY')
        
        if not api_key:
            print("⚠️  WARNING: TAVILY_API_KEY not found in environment")
            print("   SearchTool will not work without an API key")
            object.__setattr__(self, 'tavily_client', None)
            return
        
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults
            object.__setattr__(self, 'tavily_client', TavilySearchResults(max_results=10))
            print("✅ Tavily search initialized")
        except ImportError:
            print("⚠️  WARNING: langchain_community not installed")
            print("   Install with: pip install langchain-community")
            object.__setattr__(self, 'tavily_client', None)
        except Exception as e:
            print(f"⚠️  WARNING: Failed to initialize Tavily: {e}")
            object.__setattr__(self, 'tavily_client', None)
    
    def _run(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Execute a web search.
        
        Parameters:
        -----------
        query : str
            The search query
        max_results : int
            Maximum number of results (1-10)
        
        Returns:
        --------
        Dict[str, Any]
            Search results with status, message, and data
        """
        # Validate inputs
        if not query or not query.strip():
            return {
                "status": "error",
                "message": "Query cannot be empty",
                "query": query
            }
        
        # Clamp max_results
        max_results = max(1, min(10, max_results))
        
        # Check if Tavily is available
        if not self.tavily_client:
            return {
                "status": "error",
                "message": "Search service not available (TAVILY_API_KEY missing)",
                "query": query
            }
        
        try:
            print(f"🔍 Searching for: {query}")
            
            # Perform search
            results = self.tavily_client.invoke({"query": query})
            
            # Parse results
            if isinstance(results, list):
                # Limit results
                limited_results = results[:max_results]
                
                # Format results
                formatted_results = []
                for i, result in enumerate(limited_results, 1):
                    if isinstance(result, dict):
                        formatted_results.append({
                            "title": result.get("title", "No title"),
                            "url": result.get("url", ""),
                            "content": result.get("content", "")[:500],  # Limit content length
                            "score": result.get("score", 0)
                        })
                    else:
                        formatted_results.append({
                            "content": str(result)[:500]
                        })
                
                return {
                    "status": "success",
                    "message": f"Found {len(formatted_results)} results for '{query}'",
                    "query": query,
                    "results_count": len(formatted_results),
                    "data": formatted_results
                }
            
            elif isinstance(results, dict):
                # Single result or different format
                return {
                    "status": "success",
                    "message": f"Search completed for '{query}'",
                    "query": query,
                    "results_count": 1,
                    "data": results
                }
            
            else:
                # Unexpected format
                return {
                    "status": "success",
                    "message": f"Search completed for '{query}'",
                    "query": query,
                    "data": {"raw_result": str(results)[:1000]}
                }
        
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {
                "status": "error",
                "message": f"Search failed: {str(e)}",
                "query": query
            }
    
    async def _arun(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Async version - calls sync for now."""
        return self._run(query, max_results)


# Convenience function to create and use the tool
def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Quick function to perform a web search.
    
    Parameters:
    -----------
    query : str
        Search query
    max_results : int
        Max results to return
    
    Returns:
    --------
    Dict[str, Any]
        Search results
    
    Example:
    --------
    ```python
    from tools.gemini.search_tool import search_web
    
    results = search_web("latest AI news", max_results=3)
    print(results)
    ```
    """
    tool = SearchTool()
    return tool._run(query, max_results)


if __name__ == "__main__":
    # Quick test
    print("\n" + "="*70)
    print("SearchTool Quick Test")
    print("="*70)
    
    tool = SearchTool()
    
    # Test schema
    print("\n📋 Schema Info:")
    print(tool.get_schema_info())
    
    # Test search
    print("\n🔍 Test Search:")
    result = tool._run(query="Python programming", max_results=3)
    
    print(f"\nStatus: {result['status']}")
    print(f"Message: {result['message']}")
    if result['status'] == 'success' and 'data' in result:
        print(f"Results: {result['results_count']}")
        for i, item in enumerate(result['data'][:2], 1):
            print(f"\n  {i}. {item.get('title', 'N/A')}")
            print(f"     {item.get('content', '')[:100]}...")
    
    print("\n" + "="*70)
