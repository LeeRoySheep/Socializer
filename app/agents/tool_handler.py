"""
Tool Handler with OTE Compliance

LOCATION: app/agents/tool_handler.py
PURPOSE: Execute tools and format results with OTE tracking

TRACE POINTS:
    - VALIDATE: Input validation
    - TOOL_LOOKUP: Tool resolution
    - EXECUTE: Tool execution
    - FORMAT: Result formatting
    - ERROR: Error handling

DEPENDENCIES:
    - langchain_core.messages (ToolMessage)
    - app.agents.response_handler (ResponseHandler)
    
OTE COMPLIANCE:
    - Observability: All tool executions logged with timing
    - Traceability: Trace markers for execution flow
    - Evaluation: Success/failure rates per tool, execution timing
"""

import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import ToolMessage

from app.utils import get_logger, observe, traceable, evaluate
from app.agents.response_handler import ResponseHandler

# Get logger for this module
logger = get_logger(__name__)


class ToolHandler:
    """
    Tool execution handler with OTE tracking.
    
    Executes tools requested by the LLM and formats their results.
    Tracks performance metrics and success rates per tool.
    
    OTE Compliance:
        - All tool executions observed with timing
        - Trace markers show execution flow
        - Success/failure rates tracked per tool
        - Anomaly detection for slow/failing tools
    
    Attributes:
        tools_by_name: Dictionary mapping tool names to tool instances
        response_handler: ResponseHandler for formatting results
    
    Example:
        >>> handler = ToolHandler(tools, response_handler)
        >>> result = handler({"messages": [ai_message_with_tool_calls]})
        >>> print(result["messages"])
        [ToolMessage(...), ToolMessage(...)]
    """
    
    def __init__(self, tools: List, response_handler: Optional[ResponseHandler] = None):
        """
        Initialize ToolHandler with tools and response handler.
        
        Args:
            tools: List of tool instances
            response_handler: ResponseHandler for formatting (optional, creates default)
        """
        logger.trace("INIT", f"Initializing ToolHandler with {len(tools)} tools")
        
        # Create dictionary of tools by name
        self.tools_by_name = {}
        for tool in tools:
            tool_name = self._extract_tool_name(tool)
            if tool_name:
                self.tools_by_name[tool_name] = tool
        
        # Use provided handler or create default
        self.response_handler = response_handler or ResponseHandler()
        
        logger.observe(
            "init_complete",
            tool_count=len(self.tools_by_name),
            tool_names=list(self.tools_by_name.keys()),
            has_handler=bool(self.response_handler)
        )
    
    @traceable()
    def _extract_tool_name(self, tool: Any) -> Optional[str]:
        """
        Extract tool name from various tool formats.
        
        Handles:
        - Tools with .name attribute
        - Functions with __name__
        - Other callables
        
        Args:
            tool: Tool instance
            
        Returns:
            Optional[str]: Tool name or None
        """
        if hasattr(tool, "name"):
            return tool.name
        elif hasattr(tool, "__name__"):
            return tool.__name__
        else:
            logger.warning(f"Tool has no name attribute: {type(tool)}")
            return None
    
    @observe("execute_tools")
    @evaluate(detect_anomalies=True)
    def __call__(self, inputs: Dict[str, Any]) -> Dict[str, List]:
        """
        Execute tools requested in the last AIMessage.
        
        TRACE PATH:
            VALIDATE → For each tool:
                TOOL_LOOKUP → EXECUTE → FORMAT
        
        Args:
            inputs: Dictionary with "messages" key containing message history
            
        Returns:
            Dict with "messages" key containing ToolMessage results
            
        Raises:
            ValueError: If no messages in input
        """
        # TRACE POINT 1: Validation
        logger.trace("VALIDATE", f"Validating inputs, has_messages={('messages' in inputs)}")
        
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            logger.error("No message found in input")
            raise ValueError("No message found in input")
        
        # Check if message has tool calls
        if not hasattr(message, "tool_calls") or not message.tool_calls:
            logger.observe("tool_execution_complete", tool_calls=0, success=True)
            return {"messages": []}
        
        tool_count = len(message.tool_calls)
        logger.trace("VALIDATE", f"Found {tool_count} tool calls to execute")
        
        outputs = []
        for tool_call in message.tool_calls:
            tool_message = self._execute_single_tool(tool_call)
            outputs.append(tool_message)
        
        success_count = sum(1 for msg in outputs if '"error"' not in msg.content)
        logger.observe(
            "tool_execution_complete",
            tool_calls=tool_count,
            success_count=success_count,
            failure_count=tool_count - success_count,
            success=success_count == tool_count
        )
        
        return {"messages": outputs}
    
    @traceable()
    @observe("execute_single_tool")
    def _execute_single_tool(self, tool_call: Dict[str, Any]) -> ToolMessage:
        """
        Execute a single tool call.
        
        TRACE PATH:
            TOOL_LOOKUP → EXECUTE → FORMAT → Create ToolMessage
        
        Args:
            tool_call: Dictionary with tool call information
                {
                    "name": str,
                    "args": dict,
                    "id": str
                }
            
        Returns:
            ToolMessage: Result of tool execution
        """
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        
        logger.trace("TOOL_LOOKUP", f"Looking up tool: {tool_name}")
        
        # TRACE POINT 2: Tool lookup
        if tool_name not in self.tools_by_name:
            logger.warning(f"Tool not found: {tool_name}")
            error_msg = f"Tool '{tool_name}' not found. Available tools: {list(self.tools_by_name.keys())}"
            logger.observe("tool_executed", tool=tool_name, success=False, reason="not_found")
            return ToolMessage(
                content=json.dumps({"error": error_msg}),
                name=tool_name,
                tool_call_id=tool_call_id,
            )
        
        tool = self.tools_by_name[tool_name]
        logger.trace("EXECUTE", f"Executing {tool_name} with args: {str(tool_args)[:100]}")
        
        # TRACE POINT 3: Tool execution
        try:
            tool_result = self._invoke_tool(tool, tool_name, tool_args)
            logger.trace("FORMAT", f"Formatting result for {tool_name}")
            
            # TRACE POINT 4: Format result
            formatted_result = self.response_handler.format_tool_result(tool_result, tool_name)
            
            logger.observe(
                "tool_executed",
                tool=tool_name,
                success=True,
                result_length=len(str(formatted_result))
            )
            
            return ToolMessage(
                content=formatted_result,
                name=tool_name,
                tool_call_id=tool_call_id,
            )
            
        except Exception as e:
            # TRACE POINT 5: Error handling
            logger.error(f"Error executing {tool_name}: {str(e)}", exc_info=True)
            logger.observe("tool_executed", tool=tool_name, success=False, error=str(e))
            
            return ToolMessage(
                content=json.dumps({
                    "error": f"Error calling tool {tool_name}: {str(e)}"
                }),
                name=tool_name,
                tool_call_id=tool_call_id,
            )
    
    @traceable()
    def _invoke_tool(self, tool: Any, tool_name: str, tool_args: Any) -> Any:
        """
        Invoke a tool with proper argument handling.
        
        Handles different tool invocation patterns:
        - Tools with .invoke() method
        - Callable tools
        - Special cases (tavily_search)
        
        Args:
            tool: Tool instance
            tool_name: Name of the tool
            tool_args: Arguments for the tool
            
        Returns:
            Any: Tool execution result
            
        Raises:
            Exception: If tool execution fails
        """
        logger.trace("EXECUTE", f"Invoking {tool_name}, has_invoke={hasattr(tool, 'invoke')}")
        
        # Tools with invoke method
        if hasattr(tool, "invoke"):
            # Special handling for tavily_search
            if tool_name == "tavily_search":
                if isinstance(tool_args, dict) and "query" in tool_args:
                    return tool.invoke(tool_args["query"])
                elif isinstance(tool_args, str):
                    return tool.invoke(tool_args)
                else:
                    return tool.invoke(tool_args)
            else:
                # Standard invoke for other tools
                return tool.invoke(tool_args)
        
        # Callable tools
        elif callable(tool):
            if isinstance(tool_args, dict) and "query" in tool_args:
                return tool.invoke(tool_args["query"])
            else:
                return tool.invoke(tool_args)
        
        # Not callable
        else:
            error_msg = f"Tool {tool_name} is not callable"
            logger.error(error_msg)
            return {"error": error_msg}
    
    @traceable()
    def get_tool_names(self) -> List[str]:
        """
        Get list of available tool names.
        
        Returns:
            List[str]: List of tool names
        """
        return list(self.tools_by_name.keys())
    
    @traceable()
    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is available.
        
        Args:
            tool_name: Name of the tool to check
            
        Returns:
            bool: True if tool is available
        """
        return tool_name in self.tools_by_name
    
    @traceable()
    def bind_tools_to_llm(self, llm: Any) -> Any:
        """
        Bind tools to an LLM for tool calling.
        
        Args:
            llm: LLM instance to bind tools to
            
        Returns:
            Any: LLM with tools bound
        """
        logger.trace("BIND", f"Binding {len(self.tools_by_name)} tools to LLM")
        
        tools_list = list(self.tools_by_name.values())
        bound_llm = llm.bind_tools(tools_list)
        
        logger.observe("tools_bound", tool_count=len(tools_list), success=True)
        return bound_llm


# Backwards compatibility alias
BasicToolNode = ToolHandler
