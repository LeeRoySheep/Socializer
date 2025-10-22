"""
Universal Tool Manager
======================

Manages tools for all LLM providers (OpenAI, Gemini, Claude, local models).

This class uses OOP principles to provide the right tool implementation
based on the LLM provider being used.

Features:
- Provider-agnostic tool interface
- Automatic tool selection based on LLM type
- Backward compatibility with existing code
- Easy to extend with new providers

Author: AI Assistant
Date: 2025-10-22
"""

from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool


class ToolManager:
    """
    Manages tool initialization and selection for different LLM providers.
    
    Supports:
    - OpenAI (GPT-4, GPT-4o, GPT-3.5, etc.)
    - Google Gemini (Gemini 2.0, 1.5 Pro, etc.)
    - Anthropic Claude (Claude 3, etc.)
    - Local models (Ollama, etc.)
    
    Usage:
    ------
    ```python
    from tools.tool_manager import ToolManager
    
    # Initialize for a specific provider
    tool_manager = ToolManager(provider="gemini", data_manager=dm)
    
    # Get all tools for this provider
    tools = tool_manager.get_tools()
    
    # Bind to LLM
    llm_with_tools = llm.bind_tools(tools)
    ```
    """
    
    # Provider types
    PROVIDER_OPENAI = "openai"
    PROVIDER_GEMINI = "gemini"
    PROVIDER_CLAUDE = "claude"
    PROVIDER_LOCAL = "local"
    
    def __init__(
        self,
        provider: str = PROVIDER_OPENAI,
        data_manager: Any = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the ToolManager.
        
        Parameters:
        -----------
        provider : str
            LLM provider name ("openai", "gemini", "claude", "local")
        data_manager : Any
            DataManager instance for tools that need database access
        config : Optional[Dict[str, Any]]
            Additional configuration options
        """
        self.provider = self._normalize_provider(provider)
        self.data_manager = data_manager
        self.config = config or {}
        
        # Tool instances (initialized lazily)
        self._tools: Optional[List[BaseTool]] = None
        
        print(f"🔧 ToolManager initialized for provider: {self.provider}")
    
    def _normalize_provider(self, provider: str) -> str:
        """
        Normalize provider name to standard format.
        
        Parameters:
        -----------
        provider : str
            Provider name (case-insensitive)
        
        Returns:
        --------
        str
            Normalized provider name
        """
        provider_lower = provider.lower()
        
        # Map common variations to standard names
        if any(x in provider_lower for x in ['gpt', 'openai']):
            return self.PROVIDER_OPENAI
        elif any(x in provider_lower for x in ['gemini', 'google']):
            return self.PROVIDER_GEMINI
        elif any(x in provider_lower for x in ['claude', 'anthropic']):
            return self.PROVIDER_CLAUDE
        elif any(x in provider_lower for x in ['ollama', 'local']):
            return self.PROVIDER_LOCAL
        else:
            # Default to OpenAI for unknown providers
            print(f"⚠️  Unknown provider '{provider}', defaulting to OpenAI")
            return self.PROVIDER_OPENAI
    
    def get_tools(self, tool_names: Optional[List[str]] = None) -> List[BaseTool]:
        """
        Get all tools configured for this provider.
        
        Parameters:
        -----------
        tool_names : Optional[List[str]]
            Specific tool names to get. If None, returns all tools.
        
        Returns:
        --------
        List[BaseTool]
            List of tool instances
        """
        if self._tools is None:
            self._tools = self._initialize_tools()
        
        if tool_names is None:
            return self._tools
        
        # Filter to specific tools
        return [t for t in self._tools if t.name in tool_names]
    
    def _initialize_tools(self) -> List[BaseTool]:
        """
        Initialize all tools based on provider.
        
        Returns:
        --------
        List[BaseTool]
            List of initialized tool instances
        """
        if self.provider == self.PROVIDER_GEMINI:
            return self._initialize_gemini_tools()
        elif self.provider == self.PROVIDER_OPENAI:
            return self._initialize_openai_tools()
        elif self.provider == self.PROVIDER_CLAUDE:
            return self._initialize_claude_tools()
        elif self.provider == self.PROVIDER_LOCAL:
            return self._initialize_local_tools()
        else:
            # Fallback to OpenAI tools
            return self._initialize_openai_tools()
    
    def _initialize_gemini_tools(self) -> List[BaseTool]:
        """
        Initialize tools optimized for Gemini.
        
        Uses the new GeminiToolBase architecture with proper schemas.
        
        Returns:
        --------
        List[BaseTool]
            Gemini-compatible tools
        """
        print("🌟 Initializing Gemini-optimized tools...")
        tools = []
        
        # 1. Search Tool (Gemini-optimized)
        try:
            from tools.gemini.search_tool import SearchTool
            search_tool = SearchTool()
            tools.append(search_tool)
            print("  ✅ SearchTool (Gemini-optimized)")
        except Exception as e:
            print(f"  ⚠️  SearchTool failed: {e}")
        
        # 2. Conversation Recall Tool
        try:
            from tools.conversation_recall_tool import ConversationRecallTool
            if self.data_manager:
                recall_tool = ConversationRecallTool(self.data_manager)
                tools.append(recall_tool)
                print("  ✅ ConversationRecallTool")
        except Exception as e:
            print(f"  ⚠️  ConversationRecallTool failed: {e}")
        
        # TODO: Add more Gemini-optimized tools here as we migrate them
        # - SkillEvaluator (Gemini version)
        # - UserPreferenceTool (Gemini version)
        # - etc.
        
        print(f"🌟 Initialized {len(tools)} Gemini tools")
        return tools
    
    def _initialize_openai_tools(self) -> List[BaseTool]:
        """
        Initialize tools for OpenAI models.
        
        Uses existing tool implementations that work well with OpenAI.
        
        Returns:
        --------
        List[BaseTool]
            OpenAI-compatible tools
        """
        print("🤖 Initializing OpenAI tools...")
        tools = []
        
        # Import existing tools (these already work with OpenAI)
        try:
            # For now, use Gemini SearchTool - it works with all providers
            from tools.gemini.search_tool import SearchTool
            search_tool = SearchTool()
            tools.append(search_tool)
            print("  ✅ SearchTool")
        except Exception as e:
            print(f"  ⚠️  SearchTool failed: {e}")
        
        try:
            from tools.conversation_recall_tool import ConversationRecallTool
            if self.data_manager:
                recall_tool = ConversationRecallTool(self.data_manager)
                tools.append(recall_tool)
                print("  ✅ ConversationRecallTool")
        except Exception as e:
            print(f"  ⚠️  ConversationRecallTool failed: {e}")
        
        # TODO: Add other existing tools
        # These are in ai_chatagent.py and need to be migrated
        
        print(f"🤖 Initialized {len(tools)} OpenAI tools")
        return tools
    
    def _initialize_claude_tools(self) -> List[BaseTool]:
        """
        Initialize tools for Claude models.
        
        Claude has similar requirements to OpenAI, so we use the same tools.
        
        Returns:
        --------
        List[BaseTool]
            Claude-compatible tools
        """
        print("🎭 Initializing Claude tools...")
        # For now, use the same as OpenAI (Claude is similar)
        return self._initialize_openai_tools()
    
    def _initialize_local_tools(self) -> List[BaseTool]:
        """
        Initialize tools for local models (Ollama, etc.).
        
        Local models may have different capabilities, so we provide
        a minimal set of reliable tools.
        
        Returns:
        --------
        List[BaseTool]
            Tools compatible with local models
        """
        print("🏠 Initializing local model tools...")
        # For now, use the same as OpenAI
        return self._initialize_openai_tools()
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a specific tool by name.
        
        Parameters:
        -----------
        tool_name : str
            Name of the tool to get
        
        Returns:
        --------
        Optional[BaseTool]
            Tool instance or None if not found
        """
        tools = self.get_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None
    
    def list_tool_names(self) -> List[str]:
        """
        Get list of all available tool names.
        
        Returns:
        --------
        List[str]
            List of tool names
        """
        tools = self.get_tools()
        return [tool.name for tool in tools]
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        tool_count = len(self._tools) if self._tools else "?"
        return f"<ToolManager: {self.provider}, {tool_count} tools>"


# Convenience function for quick tool initialization
def get_tools_for_provider(
    provider: str,
    data_manager: Any = None
) -> List[BaseTool]:
    """
    Quick function to get tools for a specific provider.
    
    Parameters:
    -----------
    provider : str
        LLM provider name
    data_manager : Any
        DataManager instance
    
    Returns:
    --------
    List[BaseTool]
        List of tools for this provider
    
    Example:
    --------
    ```python
    from tools.tool_manager import get_tools_for_provider
    
    tools = get_tools_for_provider("gemini", dm)
    llm_with_tools = llm.bind_tools(tools)
    ```
    """
    manager = ToolManager(provider=provider, data_manager=data_manager)
    return manager.get_tools()
