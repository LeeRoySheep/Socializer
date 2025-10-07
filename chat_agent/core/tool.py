"""Base class for tools that can be used by the chat agent."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Generic, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import inspect
import logging

from pydantic import BaseModel, Field

# Type variable for tool input model
InputT = TypeVar('InputT', bound=BaseModel)


class ToolExecutionStatus(str, Enum):
    """Status of a tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ToolResult:
    """Result of a tool execution."""
    content: Any
    status: ToolExecutionStatus = ToolExecutionStatus.COMPLETED
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolError(Exception):
    """Exception raised when a tool encounters an error."""
    def __init__(self, message: str, tool_name: Optional[str] = None, **kwargs):
        self.tool_name = tool_name
        self.details = kwargs or {}
        # Store the original message without modifications
        self.original_message = message
        # Format the error message with details
        details_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        full_message = message
        if tool_name:
            full_message = f"[{tool_name}] {full_message}"
        if details_str:
            full_message = f"{full_message} ({details_str})"
        super().__init__(full_message)


class Tool(ABC, Generic[InputT]):
    """Base class for all tools that can be used by the chat agent.
    
    Subclasses should implement the `_execute` method and define an appropriate
    input model by setting the `input_model` class variable.
    """
    
    # Class variables that should be overridden by subclasses
    name: str
    description: str
    input_model: Type[BaseModel]
    
    def __init_subclass__(cls, **kwargs):
        """Validate that subclasses implement required class variables."""
        super().__init_subclass__(**kwargs)
        
        required_attrs = ['name', 'description', 'input_model']
        for attr in required_attrs:
            if not hasattr(cls, attr):
                raise TypeError(f"Tool subclass {cls.__name__} must define class variable '{attr}'")
        
        # Validate input_model is a subclass of BaseModel
        if not (isinstance(cls.input_model, type) and issubclass(cls.input_model, BaseModel)):
            raise TypeError(f"{cls.__name__}.input_model must be a subclass of pydantic.BaseModel")
    
    @property
    def schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool's input model."""
        # Use model_json_schema for Pydantic v2 compatibility
        return self.input_model.model_json_schema()
    
    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """Execute the tool with the given input data.
        
        Args:
            input_data: Dictionary containing the input data for the tool.
            
        Returns:
            ToolResult containing the result of the execution.
            
        Raises:
            ToolError: If the input data is invalid or execution fails.
        """
        try:
            # Validate input against the input model
            try:
                validated_input = self.input_model(**input_data)
            except Exception as e:
                raise ToolError(
                    f"Invalid input for tool {self.name}: {str(e)}",
                    tool_name=self.name,
                    input_data=input_data,
                    error=str(e)
                )
            
            # Execute the tool
            result = await self._execute(validated_input)
            
            # Ensure the result is a ToolResult
            if not isinstance(result, ToolResult):
                result = ToolResult(content=result)
                
            return result
            
        except Exception as e:
            if not isinstance(e, ToolError):
                # Wrap unexpected errors in a ToolError
                e = ToolError(
                    f"Error executing tool {self.name}: {str(e)}",
                    tool_name=self.name,
                    input_data=input_data,
                    error=str(e)
                )
            raise e
    
    @abstractmethod
    async def _execute(self, input_data: InputT) -> Any:
        """Execute the tool with the given input data.
        
        This method should be implemented by subclasses to provide the tool's functionality.
        
        Args:
            input_data: Validated input data for the tool.
            
        Returns:
            The result of the tool execution, which will be wrapped in a ToolResult.
            
        Raises:
            Exception: If the tool execution fails.
        """
        pass
    
    def __call__(self, **kwargs) -> Awaitable[ToolResult]:
        """Allow the tool to be called directly with keyword arguments."""
        return self.execute(kwargs)
    
    def __str__(self) -> str:
        """Return a string representation of the tool."""
        return f"{self.__class__.__name__}(name='{self.name}')"


def tool(
    name: Optional[str] = None,
    description: Optional[str] = None,
    input_model: Optional[Type[BaseModel]] = None
) -> Callable:
    """Decorator to create a Tool from a function.
    
    Example:
        @tool(
            name="get_weather",
            description="Get the current weather for a location",
            input_model=WeatherInputModel
        )
        async def get_weather(input_data: WeatherInputModel) -> str:
            return f"The weather in {input_data.location} is sunny."
    """
    def decorator(func: Callable) -> Type[Tool]:
        # Create input model if not provided
        if input_model is None:
            # Infer input model from function signature
            sig = inspect.signature(func)
            params = {
                name: (param.annotation, ... if param.default == inspect.Parameter.empty else param.default)
                for name, param in sig.parameters.items()
                if name != 'self' and name != 'cls'
            }
            
            if not params:
                # No parameters, use an empty model
                input_model_cls = type('InputModel', (BaseModel,), {})
            else:
                # Create a dynamic model with the function's parameters
                input_model_cls = type('InputModel', (BaseModel,), {
                    '__annotations__': {k: v[0] for k, v in params.items()},
                    **{k: Field(default=v[1]) for k, v in params.items()}
                })
        else:
            input_model_cls = input_model
        
        # Create a Tool subclass for this function
        tool_name = name or func.__name__
        tool_description = description or func.__doc__ or f"Tool: {tool_name}"
        
        class FunctionTool(Tool[input_model_cls]):  # type: ignore
            name = tool_name
            description = tool_description
            input_model = input_model_cls
            
            async def _execute(self, input_data: input_model_cls) -> Any:  # type: ignore
                # Pass the input data directly to the function
                # The function will receive the input_data object and can access its attributes
                return await func(input_data)
        
        # Update the class name and docstring
        FunctionTool.__name__ = f"{tool_name}_tool"
        FunctionTool.__qualname__ = f"{tool_name}_tool"
        FunctionTool.__doc__ = tool_description
        
        return FunctionTool()
    
    return decorator
